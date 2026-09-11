#!/usr/bin/env python3
"""Terminal-only, read-only commit and PR draft generator. Python >= 3.10."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ai_gitgen.errors import GitgenError
from ai_gitgen.generation import (
    CONVENTIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    Generator,
    normalize,
)
from ai_gitgen.git import collect_changes, repository_root
from ai_gitgen.safety import mask


def temperature_value(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("temperature는 0~2 사이 숫자여야 합니다.") from exc
    if not math.isfinite(number) or not 0 <= number <= 2:
        raise argparse.ArgumentTypeError("temperature는 0~2 사이 숫자여야 합니다.")
    return number


def tokens_value(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("max-tokens는 64~32768 사이 정수여야 합니다.") from exc
    if not 64 <= number <= 32768:
        raise argparse.ArgumentTypeError("max-tokens는 64~32768 사이 정수여야 합니다.")
    return number


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description="Git 변경 사항으로 검토용 커밋/PR 초안을 생성합니다.")
    commands = cli.add_subparsers(dest="command", required=True)
    for name, help_text in (("commit", "커밋 메시지 생성"), ("pr", "PR 제목/본문 초안 생성")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--model", default=DEFAULT_MODEL, help=f"기본값: {DEFAULT_MODEL}")
        command.add_argument(
            "--temperature",
            type=temperature_value,
            default=DEFAULT_TEMPERATURE,
            help=f"0~2, 기본값: {DEFAULT_TEMPERATURE}",
        )
        command.add_argument(
            "--max-tokens",
            type=tokens_value,
            default=DEFAULT_MAX_TOKENS,
            help=f"최대 출력 토큰 수, 기본값: {DEFAULT_MAX_TOKENS}",
        )
        command.add_argument(
            "--safe-mode",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="마스킹 + 최대 10파일/200줄/20,000자 전송 (기본 ON)",
        )
        command.add_argument("--convention", choices=CONVENTIONS, default="team")
    return cli


def load_api_key(root: Path) -> str:
    """Load the root .env into the environment without replacing existing values."""
    key = os.environ.get("AI_API_KEY", "").strip()
    if key:
        return key
    path = root / ".env"
    if not path.exists():
        return ""
    if path.is_symlink() or not path.is_file():
        raise GitgenError(".env는 프로젝트 루트의 일반 파일이어야 합니다.")
    try:
        if path.stat().st_size > 65_536:
            raise GitgenError(".env가 너무 큽니다. AI_API_KEY 설정만 저장하세요.")
        load_dotenv(path, override=False, interpolate=False)
        return os.getenv("AI_API_KEY", "").strip()
    except (OSError, UnicodeError) as exc:
        raise GitgenError(
            ".env를 읽을 수 없습니다. 파일 권한과 UTF-8 인코딩을 확인하세요."
        ) from exc


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    generator = None
    key = ""
    try:
        root = repository_root(Path.cwd())
        key = load_api_key(root)
        context = collect_changes(root, safe=args.safe_mode, api_key=key)
        if not context.files:
            message = (
                "변경 사항이 없습니다."
                if not context.total_files
                else "전송 가능한 변경 사항이 없습니다. 자격증명 파일/심볼릭 링크는 제외됩니다."
            )
            print(message)
            return 0
        if not key:
            raise GitgenError(
                "AI_API_KEY가 없습니다. 환경변수 또는 프로젝트 루트 .env에 설정하세요."
            )
        if not args.model.strip():
            raise GitgenError("--model은 비어 있을 수 없습니다.")
        generator = Generator(key)
        data = generator.generate(
            args.command,
            context,
            args.convention,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        draft = normalize(
            data, args.command, context, args.convention, api_key=key, safe=args.safe_mode
        )
        warnings = list(draft.repairs)
        if context.excluded_files:
            warnings.append(f"자격증명 파일/심볼릭 링크 {context.excluded_files}개를 제외했습니다.")
        if context.truncated:
            warnings.append(
                "전송 제한으로 일부 변경이 생략되었습니다. 누락 내용을 직접 보완하세요."
            )
        if args.command == "commit" and len(draft.title) > 50:
            warnings.append("커밋 제목이 권장 길이 50자를 넘습니다. 최대 72자 규칙은 충족합니다.")
        review = (
            "AI 초안입니다. 반드시 검토·수정한 뒤 직접 적용하세요. 테스트는 실행하지 않았습니다."
        )
        divider = "=" * 60
        lines = [divider, "변경 요약", divider, *(f"- {s}" for s in draft.summary)]
        lines += [
            f"수집 {context.total_files}개 / 전송 {len(context.files)}개 / "
            f"제외 {context.excluded_files}개 / 생략 {context.omitted_files}개",
            *(f"  {f['path']}" for f in context.files),
            "",
        ]
        if args.command == "commit":
            lines += [divider, "커밋 메시지 (아래 내용 복사)", divider, draft.title]
            if draft.body:
                lines += ["", draft.body]
        else:
            lines += [
                divider,
                "PR 제목",
                divider,
                draft.title,
                "",
                divider,
                "PR 본문",
                divider,
                draft.body,
            ]
        lines += [
            divider,
            *(f"안내: {w}" for w in warnings),
            review,
        ]
        print(mask("\n".join(lines), key, patterns=args.safe_mode))
        return 0
    except GitgenError as exc:
        print(f"오류: {mask(str(exc), key)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("사용자가 실행을 취소했습니다.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
