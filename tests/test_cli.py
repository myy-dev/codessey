import os

import pytest

import main
from ai_gitgen.errors import GitgenError
from ai_gitgen.generation import Generator


@pytest.mark.parametrize("command", ["commit", "pr"])
def test_no_changes_requires_no_key_and_no_api(repo, monkeypatch, capsys, command):
    monkeypatch.setattr(Generator, "generate", lambda *a, **kw: pytest.fail("Unexpected API call"))
    assert main.main([command]) == 0
    output = capsys.readouterr().out
    assert "변경 사항이 없습니다" in output


def test_safe_mode_is_on_by_default():
    args = main.parser().parse_args(["commit"])
    assert args.safe_mode is True
    assert main.parser().parse_args(["commit", "--no-safe-mode"]).safe_mode is False


def test_missing_key_actionable_error(repo, capsys):
    (repo / "app.py").write_text("changed\n")
    assert main.main(["commit"]) == 1
    error = capsys.readouterr().err
    assert "AI_API_KEY가 없습니다" in error


def test_environment_wins_and_dotenv_does_not_expand_or_execute(repo, monkeypatch):
    monkeypatch.setattr(os, "environ", os.environ.copy())
    (repo / ".env").write_text('AI_API_KEY="synthetic-${HOME}-$(touch hacked)"\n')
    assert main.load_api_key(repo) == "synthetic-${HOME}-$(touch hacked)"
    assert os.getenv("AI_API_KEY") == "synthetic-${HOME}-$(touch hacked)"
    assert not (repo / "hacked").exists()
    monkeypatch.setenv("AI_API_KEY", "synthetic-environment-key")
    assert main.load_api_key(repo) == "synthetic-environment-key"


def test_dotenv_symlink_refused(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("secret") / "env"
    outside.write_text("AI_API_KEY=synthetic\n")
    (repo / ".env").symlink_to(outside)
    with pytest.raises(GitgenError, match="일반 파일"):
        main.load_api_key(repo)


def test_legacy_dotenv_file_is_not_loaded(repo):
    (repo / ".env.local").write_text("AI_API_KEY=synthetic-legacy-key\n")
    assert main.load_api_key(repo) == ""


@pytest.mark.parametrize("safe", [True, False])
def test_cli_masks_context_before_generation(repo, monkeypatch, capsys, safe):
    key = "synthetic-runtime-key"
    monkeypatch.setenv("AI_API_KEY", key)
    (repo / "app.py").write_text(f'api_key = "{key}"\nemail = "alice@example.test"\n')
    contexts = []

    def generate(self, command, context, convention, **kwargs):
        self.calls += 1
        contexts.append(context)
        return {"title": "fix: 설정 변경", "summary": ["설정 변경"]}

    monkeypatch.setattr(Generator, "generate", generate)
    assert main.main(["commit", "--safe-mode" if safe else "--no-safe-mode"]) == 0
    assert len(contexts) == 1
    assert key not in contexts[0].diff
    assert ("alice@example.test" in contexts[0].diff) is not safe
    assert "[REDACTED]" in contexts[0].diff
    output = capsys.readouterr().out
    assert key not in output


@pytest.mark.parametrize("command", ["commit", "pr"])
def test_cli_success_one_call_and_copyable_output(repo, monkeypatch, capsys, command):
    (repo / "app.py").write_text("changed\n")
    monkeypatch.setenv("AI_API_KEY", "synthetic-local-key")
    calls = []

    def generate(self, *args, **kwargs):
        self.calls += 1
        calls.append((args, kwargs))
        return {
            "title": "feat: 동작 개선",
            "summary": ["app.py 변경 synthetic-local-key"],
            "body": ['동작 개선 api_key="test-secret"'],
            "why": ["개선 배경 확인 필요"],
            "what": ['동작 개선 api_key="test-secret"'],
            "how_to_test": ["변경된 함수를 호출하여 출력 확인"],
        }

    monkeypatch.setattr(Generator, "generate", generate)
    args = [
        command,
        "--safe-mode",
        "--model",
        "custom-model",
        "--temperature",
        "0.4",
        "--max-tokens",
        "900",
    ]
    assert main.main(args) == 0
    output = capsys.readouterr().out
    assert len(calls) == 1
    assert calls[0][1] == {"model": "custom-model", "temperature": 0.4, "max_tokens": 900}
    assert "synthetic-local-key" not in output
    assert "test-secret" not in output
    assert "[REDACTED]" in output
    assert "반드시 검토" in output
    assert "feat: 동작 개선" in output
    assert "=" * 60 in output
    assert "변경 요약" in output
    if command == "commit":
        assert "커밋 메시지 (아래 내용 복사)" in output
        assert "feat: 동작 개선\n\n- 동작 개선" in output
    else:
        assert output.index("PR 제목") < output.index("feat: 동작 개선") < output.index("PR 본문")
        for heading in ("Why", "What", "How to Test"):
            assert f"## {heading}\n- " in output


def test_cli_api_error_does_not_leak_secret(repo, monkeypatch, capsys):
    (repo / "app.py").write_text("changed\n")
    monkeypatch.setenv("AI_API_KEY", "synthetic-private-key")

    def fail(self, *a, **kw):
        self.calls += 1
        raise GitgenError("failure synthetic-private-key")

    monkeypatch.setattr(Generator, "generate", fail)
    assert main.main(["pr"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "오류: failure" in captured.err
    assert "synthetic-private-key" not in captured.err


@pytest.mark.parametrize(
    "arguments",
    [
        ["--temperature", "nan"],
        ["--temperature", "inf"],
        ["--temperature", "-0.1"],
        ["--temperature", "3"],
        ["--temperature", "oops"],
        ["--max-tokens", "0"],
        ["--max-tokens", "32769"],
        ["--max-tokens", "1.5"],
    ],
)
def test_invalid_options_exit_before_api(repo, arguments):
    with pytest.raises(SystemExit) as error:
        main.main(["commit", *arguments])
    assert error.value.code == 2
