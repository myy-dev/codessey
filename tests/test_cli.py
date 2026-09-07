import json

import pytest

import main
from ai_gitgen.errors import GitgenError
from ai_gitgen.generation import Generator


def test_no_changes_requires_no_key_and_no_api(repo, monkeypatch, capsys):
    monkeypatch.setattr(Generator, "generate", lambda *a, **kw: pytest.fail("Unexpected API call"))
    assert main.main(["commit"]) == 0
    assert "변경 사항이 없습니다" in capsys.readouterr().out
    assert main.main(["pr", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["metadata"]["api_calls"] == 0


def test_missing_key_actionable_error(repo, capsys):
    (repo / "app.py").write_text("changed\n")
    assert main.main(["commit"]) == 1
    error = capsys.readouterr().err
    assert "AI_API_KEY가 없습니다" in error
    assert "API 요청 횟수: 0" in error


def test_environment_wins_and_dotenv_does_not_expand_or_execute(repo, monkeypatch):
    (repo / ".env.local").write_text('AI_API_KEY="synthetic-${HOME}-$(touch hacked)"\n')
    assert main.load_api_key(repo) == "synthetic-${HOME}-$(touch hacked)"
    assert not (repo / "hacked").exists()
    monkeypatch.setenv("AI_API_KEY", "synthetic-environment-key")
    assert main.load_api_key(repo) == "synthetic-environment-key"


def test_dotenv_symlink_refused(repo, tmp_path_factory):
    outside = tmp_path_factory.mktemp("secret") / "env"
    outside.write_text("AI_API_KEY=synthetic\n")
    (repo / ".env.local").symlink_to(outside)
    with pytest.raises(GitgenError, match="일반 파일"):
        main.load_api_key(repo)


def test_preview_is_api_free_and_has_masked_context(repo, monkeypatch, capsys):
    (repo / "app.py").write_text('email = "alice@example.test"\n')
    monkeypatch.setattr(Generator, "generate", lambda *a, **kw: pytest.fail("Unexpected API call"))
    assert main.main(["pr", "--preview", "--safe-mode"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["metadata"]["api_calls"] == 0
    assert "alice@example.test" not in str(preview)
    assert "[REDACTED]" in str(preview)
    assert main.main(["pr", "--preview", "--no-safe-mode"]) == 0
    assert "alice@example.test" in capsys.readouterr().out


def test_preview_matches_request_and_preserves_nested_json(repo, capsys):
    from ai_gitgen.generation import build_messages
    from ai_gitgen.git import collect_changes

    (repo / "app.py").write_text('api_key = "synthetic-source-secret"\n')
    context = collect_changes(repo, safe=True)
    assert main.main(["commit", "--preview"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["messages"] == build_messages("commit", context, "team")
    inner = json.loads(preview["messages"][1]["content"])
    assert "synthetic-source-secret" not in inner["context"]["diff"]


@pytest.mark.parametrize("command", ["commit", "pr"])
@pytest.mark.parametrize("as_json", [False, True])
def test_cli_success_one_call_and_copyable_output(repo, monkeypatch, capsys, command, as_json):
    (repo / "app.py").write_text("changed\n")
    monkeypatch.setenv("AI_API_KEY", "synthetic-local-key")
    calls = []

    def generate(self, *args, **kwargs):
        self.calls += 1
        calls.append((args, kwargs))
        return {
            "title": "feat: 동작 개선",
            "summary": ["app.py 변경"],
            "body": ["동작 개선"],
            "why": ["개선 배경 확인 필요"],
            "what": ["동작 개선"],
            "how_to_test": ["변경된 함수를 호출하여 출력 확인"],
        }

    monkeypatch.setattr(Generator, "generate", generate)
    args = [command, "--model", "custom-model", "--temperature", "0.4", "--max-tokens", "900"]
    if as_json:
        args.append("--json")
    assert main.main(args) == 0
    output = capsys.readouterr().out
    assert len(calls) == 1
    assert calls[0][1] == {"model": "custom-model", "temperature": 0.4, "max_tokens": 900}
    assert "synthetic-local-key" not in output
    assert "반드시 검토" in output
    if as_json:
        data = json.loads(output)
        assert data["metadata"]["api_calls"] == 1
        assert data["title"] == "feat: 동작 개선"
    else:
        assert "=" * 60 in output
        assert "변경 요약" in output
        assert "API 요청 횟수: 1" in output
        assert ("커밋 메시지" if command == "commit" else "PR 제목") in output


def test_cli_api_error_counts_attempt_without_leaking_secret(repo, monkeypatch, capsys):
    (repo / "app.py").write_text("changed\n")
    monkeypatch.setenv("AI_API_KEY", "synthetic-private-key")

    def fail(self, *a, **kw):
        self.calls += 1
        raise GitgenError("failure synthetic-private-key")

    monkeypatch.setattr(Generator, "generate", fail)
    assert main.main(["pr", "--json"]) == 1
    output = capsys.readouterr().out
    assert json.loads(output)["api_calls"] == 1
    assert "synthetic-private-key" not in output


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
        ["--staged", "--base", "main"],
    ],
)
def test_invalid_options_exit_before_api(repo, arguments):
    with pytest.raises(SystemExit) as error:
        main.main(["commit", *arguments])
    assert error.value.code == 2


def test_json_remains_parseable_with_assignment_text(capsys):
    main.print_json({"body": 'api_key="test-secret"\n- password=other-secret'}, "", True)
    data = json.loads(capsys.readouterr().out)
    assert "test-secret" not in data["body"]
    assert "other-secret" not in data["body"]
