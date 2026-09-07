"""Read Git status/diffs only; never stage, commit, push or create a PR."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import GitgenError
from .safety import mask, sensitive_path

SAFE_FILES = 10
SAFE_LINES = 200
SAFE_CHARS = 20_000
MAX_DIFF_BYTES = 2_000_000
MAX_CONTEXT_CHARS = 200_000


def run_git(root: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> bytes:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_LITERAL_PATHSPECS="1", LC_ALL="C")
    try:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", *args],
            cwd=root,
            env=env,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitgenError("Git을 찾을 수 없습니다. Git 설치 및 PATH를 확인하세요.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitgenError(f"git {args[0]} 실행 시간이 30초를 초과했습니다.") from exc
    except OSError as exc:
        raise GitgenError(f"Git 프로세스를 실행할 수 없습니다 (OS 오류 {exc.errno}).") from exc
    if result.returncode not in allowed:
        reason = mask(result.stderr.decode("utf-8", "replace").strip())[:1000]
        raise GitgenError(f"git {args[0]} 실패 (종료 코드 {result.returncode}): {reason}")
    if len(result.stdout) > MAX_DIFF_BYTES:
        raise GitgenError(
            f"git {args[0]} 결과가 2MB를 초과했습니다. 수집할 변경의 크기를 줄이세요."
        )
    return result.stdout


def repository_root(cwd: Path) -> Path:
    raw = run_git(cwd, "rev-parse", "--show-toplevel")
    root = Path(os.fsdecode(raw).rstrip("\n")).resolve()
    if root != cwd.resolve():
        raise GitgenError(f"Git 프로젝트 루트에서 실행하세요: {mask(str(root))}")
    return root


@dataclass(frozen=True)
class Change:
    path: str
    status: str
    previous_path: str | None = None

    @property
    def paths(self) -> tuple[str, ...]:
        return (self.previous_path, self.path) if self.previous_path else (self.path,)


def parse_status(raw: bytes) -> list[Change]:
    fields = raw.split(b"\0")
    changes = []
    i = 0
    while i < len(fields) and fields[i]:
        record = fields[i]
        if len(record) < 4 or record[2:3] != b" ":
            raise GitgenError("git status 결과 형식을 해석할 수 없습니다.")
        status, path = record[:2].decode("ascii"), os.fsdecode(record[3:])
        previous = None
        if "R" in status or "C" in status:
            i += 1
            if i >= len(fields) or not fields[i]:
                raise GitgenError("git status의 이름 변경 경로가 누락되었습니다.")
            previous = os.fsdecode(fields[i])
        changes.append(Change(path, status, previous))
        i += 1
    return changes


@dataclass
class Context:
    files: list[dict[str, str]]
    diff: str
    total_files: int
    excluded_files: int
    omitted_files: int
    truncated: bool

    def as_dict(self) -> dict:
        return {
            "scope": "staged + unstaged + untracked",
            "files": self.files,
            "diff": self.diff,
            "total_files": self.total_files,
            "excluded_files": self.excluded_files,
            "omitted_files": self.omitted_files,
            "truncated": self.truncated,
            "diff_lines": len(self.diff.splitlines()),
        }


DIFF_OPTIONS = (
    "--no-ext-diff",
    "--no-textconv",
    "--no-color",
    "--no-renames",
    "--unified=3",
)


def collect_changes(root: Path, *, safe: bool, api_key: str = "") -> Context:
    changes = parse_status(
        run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    )
    excluded = 0
    eligible = []
    for change in changes:
        # Reject credentials and links in BOTH modes. Do not read targets outside the repo.
        if any(sensitive_path(p) or (root / p).is_symlink() for p in change.paths):
            excluded += 1
        else:
            eligible.append(change)
    selected = eligible[:SAFE_FILES] if safe else eligible
    files = []
    chunks: list[str] = []
    truncated = len(selected) < len(eligible)
    remaining_lines = SAFE_LINES if safe else None
    remaining_chars = SAFE_CHARS if safe else MAX_CONTEXT_CHARS
    for change in selected:
        if remaining_lines == 0 or remaining_chars <= 0:
            truncated = True
            break
        files.append(
            {
                "status": change.status,
                "path": mask(change.path, api_key, patterns=safe),
                **(
                    {"previous_path": mask(change.previous_path, api_key, patterns=safe)}
                    if change.previous_path
                    else {}
                ),
            }
        )
        pieces = []
        if change.status == "??":
            pieces.append(
                (
                    "UNTRACKED",
                    run_git(
                        root,
                        "diff",
                        "--no-index",
                        *DIFF_OPTIONS,
                        "--",
                        os.devnull,
                        change.path,
                        allowed=(0, 1),
                    ),
                )
            )
        else:
            pieces.append(
                ("STAGED", run_git(root, "diff", "--cached", *DIFF_OPTIONS, "--", *change.paths))
            )
            pieces.append(
                ("UNSTAGED", run_git(root, "diff", *DIFF_OPTIONS, "--", *change.paths))
            )
        nonempty = [(label, raw) for label, raw in pieces if raw]
        raw_text = (
            "\n".join(
                f"[{label}]\n{raw.decode('utf-8', 'replace').rstrip()}" for label, raw in nonempty
            )
            or "[내용 diff 없음: 빈 파일, 파일 모드 또는 서브모듈 상태 변경을 확인하세요.]"
        )
        # Mask complete text BEFORE truncation, so cut private key blocks cannot escape.
        cleaned = mask(raw_text, api_key, patterns=safe)
        lines = cleaned.splitlines()
        if remaining_lines is not None and len(lines) > remaining_lines:
            lines = lines[:remaining_lines]
            truncated = True
        text = "\n".join(lines)
        if len(text) + 1 > remaining_chars:
            text = text[: max(0, remaining_chars - 1)]
            truncated = True
        chunks.append(text)
        remaining_chars -= len(text) + 1
        if remaining_lines is not None:
            remaining_lines -= len(text.splitlines())
    return Context(
        files,
        "\n".join(chunks),
        len(changes),
        excluded,
        len(eligible) - len(files),
        truncated,
    )
