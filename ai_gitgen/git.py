"""Git 상태와 diff를 읽기 전용으로 수집한다."""

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
    """Git 명령을 실행하고 종료 코드와 출력 크기를 검증한다."""
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
    """Git 저장소 루트를 조회하고 루트에서 실행 중인지 검증한다."""
    raw = run_git(cwd, "rev-parse", "--show-toplevel")
    root = Path(os.fsdecode(raw).rstrip("\n")).resolve()
    if root != cwd.resolve():
        raise GitgenError(f"Git 프로젝트 루트에서 실행하세요: {mask(str(root))}")
    return root


@dataclass(frozen=True)
class Change:
    """변경된 파일의 현재 경로, 상태와 이전 경로를 보관한다."""

    path: str
    status: str
    previous_path: str | None = None

    @property
    def paths(self) -> tuple[str, ...]:
        """현재 경로와 이름 변경 전 경로를 반환한다."""
        return (self.previous_path, self.path) if self.previous_path else (self.path,)


def parse_status(raw: bytes) -> list[Change]:
    """NUL로 구분된 Git 상태 출력을 변경 파일 목록으로 변환한다."""
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
    """AI에 전달할 Git 변경 내용과 수집 결과 통계를 보관한다."""

    files: list[dict[str, str]]
    diff: str
    total_files: int
    excluded_files: int
    omitted_files: int
    truncated: bool

    def as_dict(self) -> dict:
        """Git 변경 컨텍스트를 API 전송용 딕셔너리로 변환한다."""
        return {
            "scope": "Git 변경 사항",
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
    """미커밋 Git 변경을 수집하고 선택한 안전 정책을 적용한다."""

    # Git 변경 상태 수집 및 최초 커밋 존재 여부 확인
    changes = parse_status(
        run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    )
    has_head = bool(run_git(root, "rev-parse", "--verify", "HEAD", allowed=(0, 128)).strip())

    # 안전 모드와 관계없는 민감 파일·심볼릭 링크 공통 제외
    excluded = 0
    eligible = []
    for change in changes:
        if any(sensitive_path(p) or (root / p).is_symlink() for p in change.paths):
            excluded += 1
        else:
            eligible.append(change)

    # 안전 모드별 파일 선택 및 전체 전송 한도 초기화
    selected = eligible[:SAFE_FILES] if safe else eligible
    files = []
    chunks: list[str] = []
    truncated = len(selected) < len(eligible)
    remaining_lines = SAFE_LINES if safe else None
    remaining_chars = SAFE_CHARS if safe else MAX_CONTEXT_CHARS

    # 선택 파일별 메타데이터와 diff 수집
    for change in selected:
        if remaining_lines == 0 or remaining_chars <= 0:
            truncated = True
            break
        files.append(
            {
                "path": mask(change.path, api_key, patterns=safe),
                **(
                    {"previous_path": mask(change.previous_path, api_key, patterns=safe)}
                    if change.previous_path
                    else {}
                ),
            }
        )

        # 미추적 파일·최초 커밋 이전 파일의 빈 파일 기준 diff 생성
        if change.status == "??" or not has_head:
            if (root / change.path).exists():
                raw = run_git(
                    root,
                    "diff",
                    "--no-index",
                    *DIFF_OPTIONS,
                    "--",
                    os.devnull,
                    change.path,
                    allowed=(0, 1),
                )
            else:
                raw = b""
        else:
            # 추적 파일의 HEAD 기준 staged·unstaged diff 생성
            raw = run_git(root, "diff", "HEAD", *DIFF_OPTIONS, "--", *change.paths)

        # diff 디코딩 및 내용 없는 변경 안내 구성
        raw_text = raw.decode("utf-8", "replace").rstrip() or (
            "[내용 diff 없음: 빈 파일, 파일 모드 또는 서브모듈 상태 변경을 확인하세요.]"
        )

        # 잘린 개인 키 노출 방지를 위한 전체 원문 마스킹 후 길이 제한
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

    # 수집 결과와 제외·생략 통계를 포함한 전송 컨텍스트 구성
    return Context(
        files,
        "\n".join(chunks),
        len(changes),
        excluded,
        len(eligible) - len(files),
        truncated,
    )
