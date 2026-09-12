import json

import httpx
import pytest
from openai import OpenAI

from ai_gitgen import generation
from ai_gitgen.errors import GitgenError
from ai_gitgen.generation import Draft, Generator, normalize, validate
from ai_gitgen.git import Context


@pytest.fixture
def context():
    # 테스트용 변경 정보 생성.
    return Context([{"path": "app.py"}], "+new behavior", 1, 0, 0, False)


@pytest.fixture
def install_transport(monkeypatch):
    # API 모의 응답 및 호출 기록 도구 준비.
    calls = []
    options = []

    def install(handler):
        # 응답 처리기 연결 및 호출 기록 반환.
        def record(request):
            # HTTP 요청 기록 후 응답 처리기 호출.
            calls.append(request)
            return handler(request)

        def factory(**kwargs):
            # 생성 옵션 기록 및 모의 통신 클라이언트 생성.
            options.append(kwargs)
            return OpenAI(http_client=httpx.Client(transport=httpx.MockTransport(record)), **kwargs)

        monkeypatch.setattr(generation, "OpenAI", factory)
        return calls, options

    return install


def completion(data, *, reason="stop", refusal=None):
    # 테스트용 API 응답 생성.
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 0,
            "model": "gpt-4.1-mini",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": reason,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(data),
                        "refusal": refusal,
                    },
                }
            ],
        },
    )


def invoke(generator, context, command="commit"):
    # 기본 테스트 옵션으로 초안 생성 호출.
    return generator.generate(
        command, context, "team", model="gpt-4.1-mini", temperature=0.2, max_tokens=1200
    )


@pytest.mark.parametrize("command", ["commit", "pr"])
def test_real_sdk_serializes_options_and_exactly_one_request(context, install_transport, command):
    # 실제 SDK 요청 구성 및 1회 호출 제한 검증.
    context.diff += '\n+api_key = "[REDACTED]"'
    data = {"title": "feat: 동작 추가", "summary": ["새 동작"], "body": ["app.py 개선"]}
    calls, options = install_transport(lambda _: completion(data))
    generator = Generator("synthetic-test-key")
    assert invoke(generator, context, command) == data
    assert generator.calls == len(calls) == 1
    payload = json.loads(calls[0].content)
    assert str(calls[0].url) == "https://api.openai.com/v1/chat/completions"
    assert payload["temperature"] == 0.2
    assert payload["max_completion_tokens"] == 1200
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["response_format"]["json_schema"]["strict"] is True
    schema = payload["response_format"]["json_schema"]["schema"]
    fields = {"title", "summary"} | (
        {"body"} if command == "commit" else {"why", "what", "how_to_test"}
    )
    assert set(schema["properties"]) == set(schema["required"]) == fields
    assert schema["additionalProperties"] is False
    assert payload["store"] is False
    assert "new behavior" in payload["messages"][1]["content"]
    request_context = json.loads(payload["messages"][1]["content"])["context"]
    assert request_context["diff"] == context.diff
    assert "신뢰하지" in payload["messages"][0]["content"]
    assert options[0]["max_retries"] == 0
    with pytest.raises(GitgenError, match="1회"):
        invoke(generator, context)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "status,message",
    [
        (400, "옵션"),
        (401, "인증 실패"),
        (403, "권한"),
        (404, "모델"),
        (429, "크레딧"),
        (500, "서버"),
    ],
)
def test_errors_do_not_retry_or_echo_api_bodies(context, install_transport, status, message):
    # API 오류의 재시도·응답 본문 노출 방지 검증.
    calls, _ = install_transport(
        lambda _: httpx.Response(
            status, json={"error": {"message": "secret-source-never-print", "type": "error"}}
        )
    )
    generator = Generator("synthetic-test-key")
    with pytest.raises(GitgenError, match=message) as error:
        invoke(generator, context)
    assert "secret-source-never-print" not in str(error.value)
    assert generator.calls == len(calls) == 1


@pytest.mark.parametrize(
    "error,message",
    [
        (httpx.ConnectError, "네트워크"),
        (httpx.ReadTimeout, "30초"),
    ],
)
def test_network_and_timeout(context, install_transport, error, message):
    # 네트워크·시간 초과 오류 안내 검증.
    def fail(request):
        # HTTP 통신 오류 재현.
        raise error("synthetic failure", request=request)

    calls, _ = install_transport(fail)
    with pytest.raises(GitgenError, match=message):
        invoke(Generator("test-key"), context)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "data,reason,refusal,message",
    [
        ({}, "length", None, "잘렸"),
        ({}, "stop", "Refused", "거절"),
        ({}, "content_filter", None, "거절"),
        ([], "stop", None, "JSON 객체"),
        ({}, "tool_calls", None, "완성되지"),
    ],
)
def test_incomplete_or_refused_response_fails_without_fabricated_draft(
    context, install_transport, data, reason, refusal, message
):
    # 불완전·거절 응답의 초안 생성 실패 검증.
    calls, _ = install_transport(lambda _: completion(data, reason=reason, refusal=refusal))
    with pytest.raises(GitgenError, match=message):
        invoke(Generator("test-key"), context)
    assert len(calls) == 1


def test_invalid_json_response(context, install_transport):
    # 잘못된 JSON 응답 거부 검증.
    def respond(_):
        # JSON 형식 위반 응답 생성.
        response = completion({})
        data = response.json()
        data["choices"][0]["message"]["content"] = "this is not JSON"
        return httpx.Response(200, json=data)

    install_transport(respond)
    with pytest.raises(GitgenError, match="올바른 JSON"):
        invoke(Generator("test-key"), context)


@pytest.mark.parametrize("choices", [[], [{}]])
def test_malformed_api_envelope_has_actionable_error(context, install_transport, choices):
    # 생성 결과·메시지 누락 안내 검증.
    calls, _ = install_transport(lambda _: httpx.Response(200, json={"choices": choices}))
    with pytest.raises(GitgenError, match="생성 결과|메시지"):
        invoke(Generator("test-key"), context)
    assert len(calls) == 1


def test_commit_normalizes_title_and_limits_body(context):
    # 커밋 제목 보정 및 본문 불릿 제한 검증.
    draft = normalize(
        {
            "title": "# 제목\n" + "가" * 100,
            "summary": ["변경 요약"],
            "body": ["one", "two", "three", "four"],
        },
        "commit",
        context,
        "team",
        api_key="",
        safe=True,
    )
    assert len(draft.title) <= 72
    assert draft.title.startswith("chore: ")
    assert "\n" not in draft.title
    assert len(draft.body.splitlines()) == 2
    assert draft.repairs
    assert validate(draft) == []


def test_pr_repairs_all_required_sections(context):
    # PR 제목 길이 및 필수 섹션 보정 검증.
    draft = normalize({"title": "나" * 100}, "pr", context, "none", api_key="", safe=True)
    assert len(draft.title) <= 80
    assert validate(draft) == []
    for section in ("Why", "What", "How to Test"):
        assert f"## {section}\n- " in draft.body
    assert "미실행:" in draft.body
    assert len(draft.repairs) >= 4


@pytest.mark.parametrize("command", ["commit", "pr"])
def test_empty_malformed_fields_have_explicit_repairs(context, command):
    # 누락·형식 오류 필드 보완 및 보정 기록 검증.
    draft = normalize(
        {"title": None, "summary": 42, "body": {}, "why": [], "what": 0, "how_to_test": False},
        command,
        context,
        "none",
        api_key="",
        safe=True,
    )
    assert validate(draft) == []
    assert "보완" in " ".join(draft.repairs)


def test_validator_rejects_bad_titles_sections_and_body():
    # 제목·섹션·본문 규칙 위반 검출 검증.
    for draft in (
        Draft("commit", "x" * 73, ["summary"], "", []),
        Draft("pr", "x" * 81, ["summary"], "", []),
        Draft("pr", "multi\nline", [], "## Why\nno bullet", []),
        Draft("commit", "title", ["summary"], "not bullets", []),
    ):
        assert validate(draft)
    sections = ("Why", "What", "How to Test")
    for invalid_section in sections:
        for invalid_body in ("", f"## {invalid_section}\n불릿 없는 본문"):
            body = "\n\n".join(
                invalid_body if section == invalid_section else f"## {section}\n- 내용"
                for section in sections
            )
            draft = Draft("pr", "유효한 제목", ["요약"], body, [])
            assert validate(draft) == [f"{invalid_section} 섹션에 불릿이 없습니다."]


def test_convention_before_and_after(context):
    # 컨벤션 적용 전·후 제목 비교.
    data = {"title": "입력 검증 추가", "summary": ["입력 검증"], "body": []}
    plain = normalize(data, "commit", context, "none", api_key="", safe=True)
    team = normalize(data, "commit", context, "team", api_key="", safe=True)
    assert plain.title == "입력 검증 추가"
    assert team.title == "chore: 입력 검증 추가"


def test_output_masks_secret_and_terminal_escape(context):
    # 초안 출력의 민감정보·터미널 제어 문자 제거 검증.
    secret = "synthetic-runtime-key"
    draft = normalize(
        {
            "title": f"fix: {secret}\x1b[31m",
            "summary": ["a@example.test"],
            "body": [secret],
        },
        "commit",
        context,
        "team",
        api_key=secret,
        safe=True,
    )
    output = "\n".join([draft.title, *draft.summary, draft.body])
    assert secret not in output
    assert "a@example.test" not in output
    assert "\x1b" not in draft.title
