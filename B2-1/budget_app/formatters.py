"""외부 라이브러리 없는 콘솔 표와 요약 출력"""

from __future__ import annotations

import unicodedata
from typing import Iterable, Sequence

from .models import RecurringRule, Transaction
from .services import SummaryResult


def _display_width(value: str) -> int:
    """한글·전각 문자를 고려한 터미널 표시 너비 계산"""
    return sum(2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1 for character in value)


def _pad(value: str, width: int) -> str:
    """표시 너비에 맞춘 문자열 오른쪽 공백 채우기"""
    return value + " " * max(0, width - _display_width(value))


def _fixed_row(values: Sequence[str], widths: Sequence[int]) -> str:
    """최소 열 너비 유지 및 내용 잘림 없는 표 한 행 생성"""
    return " | ".join(
        _pad(value, widths[index])
        for index, value in enumerate(values)
    )


def _transaction_values(transaction: Transaction) -> tuple[str, ...]:
    """거래 한 건의 표 출력용 문자열 값 변환"""
    return (
        transaction.id,
        transaction.date,
        transaction.type,
        transaction.category,
        f"{transaction.amount:,}",
        transaction.memo,
        ",".join(transaction.tags),
    )


def make_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """헤더와 행의 열 너비에 맞춘 텍스트 표 생성"""
    string_rows = [[str(value) for value in row] for row in rows]
    if not string_rows:
        return ""
    normalized_headers = [str(header) for header in headers]
    widths = [
        max(_display_width(normalized_headers[index]), *(_display_width(row[index]) for row in string_rows))
        for index in range(len(normalized_headers))
    ]
    header_line = " | ".join(_pad(value, widths[index]) for index, value in enumerate(normalized_headers))
    separator = "-+-".join("-" * width for width in widths)
    body = [
        " | ".join(_pad(value, widths[index]) for index, value in enumerate(row))
        for row in string_rows
    ]
    return "\n".join((header_line, separator, *body))


def iter_transaction_lines(transactions: Iterable[Transaction]) -> Iterable[str]:
    """거래 한 건 선행 읽기 및 고정 너비 표 줄의 지연 생성"""
    iterator = iter(transactions)
    first = next(iterator, None)
    if first is None:
        return

    headers = ("ID", "DATE", "TYPE", "CATEGORY", "AMOUNT", "MEMO", "TAGS")
    widths = (9, 10, 7, 20, 15, 30, 40)
    yield _fixed_row(headers, widths)
    yield "-+-".join("-" * width for width in widths)

    yield _fixed_row(_transaction_values(first), widths)
    for transaction in iterator:
        yield _fixed_row(_transaction_values(transaction), widths)


def format_summary(summary: SummaryResult) -> str:
    """월별 요약의 읽기 쉬운 한국어 문자열 변환"""
    lines = [
        f"총 수입: {summary.income:,}원",
        f"총 지출: {summary.expense:,}원",
        f"잔액: {summary.balance:,}원",
    ]
    if summary.budget is not None:
        lines.append(f"예산: {summary.budget:,}원 (사용률 {summary.budget_usage:.1f}%)")
        if summary.over_budget:
            lines.append(f"[경고] 예산을 {summary.expense - summary.budget:,}원 초과했습니다.")

    if summary.income == 0 and summary.expense == 0:
        lines.append("데이터 없음")
        return "\n".join(lines)

    lines.append("")
    lines.append(f"지출 TOP {summary.top_limit}")
    if not summary.top_expenses:
        lines.append("지출 내역 없음")
    else:
        for rank, (category, amount) in enumerate(summary.top_expenses, start=1):
            lines.append(f"{rank}) {category} {amount:,}원")
    return "\n".join(lines)


def format_recurring_rules(rules: Iterable[RecurringRule]) -> str:
    """반복 거래 규칙의 정렬된 표 생성"""
    rows = [
        (
            rule.id,
            rule.type,
            rule.category,
            f"{rule.amount:,}",
            rule.day,
            rule.memo,
            ",".join(rule.tags),
        )
        for rule in rules
    ]
    return make_table(("ID", "TYPE", "CATEGORY", "AMOUNT", "DAY", "MEMO", "TAGS"), rows)
