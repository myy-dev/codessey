import pytest

from ai_gitgen.errors import GitgenError
from ai_gitgen.git import collect_changes, parse_status, repository_root
from tests.conftest import git


def test_clean_and_root(repo):
    # 변경 없는 저장소 및 루트 실행 조건 검증.
    assert repository_root(repo) == repo
    context = collect_changes(repo, safe=True)
    assert context.total_files == 0
    assert context.files == []
    child = repo / "child"
    child.mkdir()
    with pytest.raises(GitgenError, match="루트"):
        repository_root(child)


def test_non_repository(tmp_path):
    # Git 저장소 외부 실행 오류 검증.
    with pytest.raises(GitgenError, match="git rev-parse 실패.*not a git repository"):
        repository_root(tmp_path)


def test_git_changes_and_no_mutations(repo):
    # 스테이징·미스테이징·미추적 변경 수집 및 저장소 불변 검증.
    (repo / "app.py").write_text("staged_change\n")
    git(repo, "add", "app.py")
    (repo / "app.py").write_text("staged_change\nunstaged_change\n")
    (repo / "new file 한글.txt").write_text("new_content\n")
    before = git(repo, "status", "--porcelain=v1", "-z")
    index = (repo / ".git" / "index").read_bytes()
    context = collect_changes(repo, safe=True)
    assert context.total_files == 2
    assert "staged_change" in context.diff
    assert "unstaged_change" in context.diff
    assert "new_content" in context.diff
    assert context.as_dict()["scope"] == "Git 변경 사항"
    assert all("status" not in file for file in context.files)
    assert git(repo, "status", "--porcelain=v1", "-z") == before
    assert (repo / ".git" / "index").read_bytes() == index


def test_renamed_deleted_empty_and_binary(repo):
    # 이름 변경·빈 파일·바이너리 수집 검증.
    git(repo, "mv", "app.py", "renamed file.py")
    (repo / "empty.txt").touch()
    (repo / "image.bin").write_bytes(b"\0binary\xff\0")
    context = collect_changes(repo, safe=True)
    rename = next(f for f in context.files if f["path"] == "renamed file.py")
    assert rename["previous_path"] == "app.py"
    assert "Binary files" in context.diff
    assert "빈 파일" in context.diff or "new file mode" in context.diff
    assert len(context.files) == 3


def test_deleted_file(repo):
    # 삭제 파일 diff 수집 검증.
    (repo / "app.py").unlink()
    context = collect_changes(repo, safe=True)
    assert context.files[0]["path"] == "app.py"
    assert "deleted file mode" in context.diff


def test_initial_repository_without_head(tmp_path, monkeypatch):
    # 첫 커밋 이전 저장소 변경 수집 검증.
    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init")
    (tmp_path / "initial.py").write_text("initial = True\n")
    git(tmp_path, "add", "initial.py")
    assert "initial = True" in collect_changes(tmp_path, safe=True).diff


def test_literal_pathspec_filename(repo):
    # 패턴 문자 포함 파일명의 원문 처리 검증.
    (repo / "[abc].txt").write_text("literal_only\n")
    (repo / "a.txt").write_text("another\n")
    context = collect_changes(repo, safe=True)
    assert "literal_only" in context.diff
    assert "another" in context.diff


def test_status_parses_newline_and_rename_names():
    # 특수 문자 및 이름 변경 경로 해석 검증.
    changes = parse_status(b"R  new\nfile\0old\tfile\0?? --file\0")
    assert changes[0].path == "new\nfile"
    assert changes[0].previous_path == "old\tfile"
    assert changes[1].path == "--file"


@pytest.mark.parametrize("raw", [b"broken\0", b"R  missing-old\0"])
def test_invalid_status(raw):
    # 잘못된 Git 상태 출력 거부 검증.
    with pytest.raises(GitgenError):
        parse_status(raw)


def test_safe_limits_apply_to_files_diff_and_long_lines(repo):
    # 안전 모드 파일·줄·문자 수 제한 검증.
    for i in range(12):
        (repo / f"file-{i:02}.txt").write_text("line\n" * 2)
    context = collect_changes(repo, safe=True)
    assert len(context.files) == 10
    assert context.omitted_files == 2
    assert context.truncated
    (repo / "file-00.txt").write_text("many\n" * 300)
    context = collect_changes(repo, safe=True)
    assert len(context.diff.splitlines()) <= 200
    assert context.truncated
    (repo / "file-00.txt").write_text("x" * 30_000)
    context = collect_changes(repo, safe=True)
    assert len(context.diff) <= 20_000
    assert context.truncated


def test_credential_files_and_links_excluded_in_both_modes(repo, tmp_path_factory):
    # ON/OFF 공통 민감 파일·링크 제외 검증.
    (repo / ".env.secret").write_text("very_private_text\n")
    (repo / "private.pem").write_text("very_private_text\n")
    outside = tmp_path_factory.mktemp("outside") / "private.txt"
    outside.write_text("very_private_text\n")
    (repo / "link.txt").symlink_to(outside)
    (repo / "ok.txt").write_text("public\n")
    for safe in (True, False):
        context = collect_changes(repo, safe=safe)
        assert context.excluded_files == 3
        assert [f["path"] for f in context.files] == ["ok.txt"]
        assert "very_private_text" not in context.diff


def test_safe_masks_metadata_and_contents_before_truncation(repo):
    # 길이 제한 전 파일명·전체 내용 마스킹 검증.
    key = "sk-proj-" + "synthetic" * 5
    (repo / "alice@example.test.txt").write_text(
        f"key = '{key}'\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        + "private_payload\n" * 230
        + "-----END RSA PRIVATE KEY-----\n"
    )
    context = collect_changes(repo, safe=True, api_key=key)
    assert key not in context.diff
    assert "private_payload" not in context.diff
    assert "alice@example.test" not in str(context.as_dict())
    unsafe = collect_changes(repo, safe=False, api_key=key)
    assert key not in unsafe.diff
    assert "private_payload" in unsafe.diff


def test_git_external_diff_is_never_executed(repo):
    # 외부 diff 프로그램 실행 방지 검증.
    marker = repo / "external-ran"
    script = repo / "external.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
    script.chmod(0o700)
    git(repo, "config", "diff.external", str(script))
    (repo / "app.py").write_text("changed\n")
    collect_changes(repo, safe=True)
    assert not marker.exists()
