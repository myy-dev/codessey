"""CLI와 서비스에서 공유하는 입력값 검증 함수."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from .errors import ValidationError

TRANSACTION_TYPES = frozenset({"income", "expense"})


def validate_date(value: str | None) -> str:
    """날짜 문자열이 YYYY-MM-DD 형식의 실제 날짜인지 확인한다."""
    if not isinstance(value, str) or not value:
        raise ValidationError("날짜는 비어 있을 수 없습니다.", "예: 2024-01-15")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).",
            "예: 2024-01-15",
        ) from exc
    if parsed.strftime("%Y-%m-%d") != value:
        raise ValidationError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2024-01-15")
    return value


def validate_month(value: str | None) -> str:
    """월 문자열이 YYYY-MM 형식인지 확인한다."""
    if not isinstance(value, str) or not value:
        raise ValidationError("월은 비어 있을 수 없습니다.", "예: 2024-01")
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise ValidationError("월 형식이 올바르지 않습니다 (YYYY-MM).", "예: 2024-01") from exc
    if parsed.strftime("%Y-%m") != value:
        raise ValidationError("월 형식이 올바르지 않습니다 (YYYY-MM).", "예: 2024-01")
    return value


def validate_amount(value: int | str | None) -> int:
    """금액을 0보다 큰 정수로 변환한다."""
    try:
        amount = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("금액은 양의 정수여야 합니다.", "예: 15000") from exc
    if amount <= 0:
        raise ValidationError("금액은 0보다 커야 합니다.", "예: 15000")
    return amount


def validate_positive_int(value: int | str, field_name: str) -> int:
    """일반적인 양의 정수 옵션을 검증한다."""
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name}은(는) 양의 정수여야 합니다.") from exc
    if number <= 0:
        raise ValidationError(f"{field_name}은(는) 0보다 커야 합니다.")
    return number


def validate_transaction_type(value: str | None) -> str:
    """거래 타입이 income 또는 expense인지 확인한다."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("거래 타입은 비어 있을 수 없습니다.", "income 또는 expense를 입력하세요.")
    normalized = value.strip().lower()
    if normalized not in TRANSACTION_TYPES:
        raise ValidationError("거래 타입은 income 또는 expense여야 합니다.", "예: expense")
    return normalized


def validate_category_name(value: str | None) -> str:
    """카테고리 이름을 정리하고 빈 값을 거부한다."""
    if not isinstance(value, str):
        raise ValidationError("카테고리 이름은 비어 있을 수 없습니다.")
    normalized = value.strip()
    if not normalized:
        raise ValidationError("카테고리 이름은 비어 있을 수 없습니다.")
    if len(normalized) > 50:
        raise ValidationError("카테고리 이름은 50자 이하여야 합니다.")
    return normalized


def validate_day(value: int | str) -> int:
    """반복 거래의 일자를 1일부터 31일 사이로 제한한다."""
    day = validate_positive_int(value, "반복 일자")
    if day > 31:
        raise ValidationError("반복 일자는 1부터 31 사이여야 합니다.")
    return day


def parse_tags(value: str | Iterable[str] | None) -> tuple[str, ...]:
    """쉼표 문자열 또는 문자열 목록을 중복 없는 태그 튜플로 변환한다."""
    if value is None:
        return ()
    raw_tags = value.split(",") if isinstance(value, str) else value
    result: list[str] = []
    seen: set[str] = set()
    for raw_tag in raw_tags:
        tag = str(raw_tag).strip()
        if tag and tag not in seen:
            seen.add(tag)
            result.append(tag)
    return tuple(result)


def validate_date_range(from_date: str | None, to_date: str | None) -> tuple[str | None, str | None]:
    """선택적 시작일과 종료일의 형식 및 순서를 확인한다."""
    start = validate_date(from_date) if from_date else None
    end = validate_date(to_date) if to_date else None
    if start and end and start > end:
        raise ValidationError("시작일은 종료일보다 늦을 수 없습니다.")
    return start, end


def validate_existing_file(path: Path) -> Path:
    """가져오기 대상이 읽을 수 있는 파일인지 확인한다."""
    if not path.exists() or not path.is_file():
        raise ValidationError(f"파일을 찾을 수 없습니다: {path}", "--from 경로를 확인하세요.")
    return path
