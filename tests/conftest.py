from __future__ import annotations

import subprocess

import pytest


@pytest.fixture
def repo(tmp_path, monkeypatch):
    # API 키 환경변수 제거 및 테스트 저장소 생성.
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Test Author")
    git(tmp_path, "config", "user.email", "author@example.test")
    git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("def greeting():\n    return 'hello'\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "feat: 인사 함수 추가")
    return tmp_path


def git(root, *args):
    # 테스트용 Git 명령 실행.
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True).stdout
