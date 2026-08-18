"""argparse 기반 명령행 인터페이스."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Iterable, Sequence, TypeVar

from .decorators import handle_cli_errors, log_execution
from .errors import BudgetAppError, ValidationError
from .formatters import format_recurring_rules, format_summary, iter_transaction_lines
from .models import Transaction
from .services import BudgetService
from .validators import validate_amount, validate_date, validate_transaction_type

T = TypeVar("T")


class FriendlyArgumentParser(argparse.ArgumentParser):
    """인자 오류를 애플리케이션 형식으로 변환하는 파서."""

    def error(self, message: str) -> None:
        raise ValidationError(f"명령어 옵션이 올바르지 않습니다: {message}")


def _prompt_until(prompt: str, validator: Callable[[str], T]) -> T:
    """입력값이 검증을 통과할 때까지 오류와 힌트를 보여 주며 재입력받는다."""
    while True:
        value = input(prompt)
        try:
            return validator(value)
        except BudgetAppError as exc:
            print(f"[오류] {exc.message}")
            if exc.hint:
                print(f"[힌트] {exc.hint}")


def _registered_category(service: BudgetService, value: str) -> str:
    """대화형 입력의 카테고리가 등록되어 있는지 확인한다."""
    normalized = value.strip()
    if normalized not in service.list_categories():
        raise ValidationError(
            f"등록되지 않은 카테고리입니다: {normalized}",
            "목록에서 선택하거나 category add로 먼저 등록하세요.",
        )
    return normalized


def _print_transactions(transactions: Iterable[Transaction]) -> None:
    """거래를 한 줄씩 출력해 전체 결과를 메모리에 쌓지 않는다."""
    printed = False
    for line in iter_transaction_lines(transactions):
        print(line)
        printed = True
    if not printed:
        print("표시할 거래가 없습니다.")


def _handle_add(args: argparse.Namespace, service: BudgetService) -> int:
    """대화형으로 거래를 추가한다."""
    del args
    date = _prompt_until("날짜(YYYY-MM-DD): ", validate_date)
    transaction_type = _prompt_until("타입(income/expense): ", validate_transaction_type)
    categories = ", ".join(service.list_categories())
    category = _prompt_until(
        f"카테고리({categories}): ",
        lambda value: _registered_category(service, value),
    )
    amount = _prompt_until("금액(양수): ", validate_amount)
    memo = input("메모(선택): ")
    tags = input("태그(쉼표로 구분, 없으면 엔터): ")
    transaction = service.add_transaction(
        date=date,
        transaction_type=transaction_type,
        category=category,
        amount=amount,
        memo=memo,
        tags=tags,
    )
    print(f"[저장 완료] id={transaction.id}")
    return 0


def _handle_list(args: argparse.Namespace, service: BudgetService) -> int:
    """최근 거래를 출력한다."""
    _print_transactions(service.list_transactions(args.limit))
    return 0


def _handle_search(args: argparse.Namespace, service: BudgetService) -> int:
    """조건에 맞는 거래를 출력한다."""
    transactions = service.search_transactions(
        from_date=args.from_date,
        to_date=args.to_date,
        category=args.category,
        transaction_type=args.transaction_type,
        query=args.query,
        tag=args.tag,
    )
    _print_transactions(transactions)
    return 0


def _handle_summary(args: argparse.Namespace, service: BudgetService) -> int:
    """월별 요약을 출력한다."""
    print(format_summary(service.summarize(args.month, args.top)))
    return 0


def _handle_budget_set(args: argparse.Namespace, service: BudgetService) -> int:
    """월 예산을 저장한다."""
    amount = service.set_budget(args.month, args.amount)
    print(f"[저장 완료] {args.month} 예산 {amount:,}원")
    return 0


def _handle_budget_get(args: argparse.Namespace, service: BudgetService) -> int:
    """월 예산을 조회한다."""
    amount = service.get_budget(args.month)
    if amount is None:
        print(f"{args.month}에 설정된 예산이 없습니다.")
    else:
        print(f"{args.month} 예산: {amount:,}원")
    return 0


def _category_name(args: argparse.Namespace, prompt: str) -> str:
    """옵션 또는 대화형 입력에서 카테고리명을 얻는다."""
    return args.name if args.name is not None else input(prompt)


def _handle_category_add(args: argparse.Namespace, service: BudgetService) -> int:
    """카테고리를 추가한다."""
    category = service.add_category(_category_name(args, "카테고리명: "))
    print(f"[저장 완료] category={category}")
    return 0


def _handle_category_list(args: argparse.Namespace, service: BudgetService) -> int:
    """카테고리 목록을 출력한다."""
    del args
    for category in service.list_categories():
        print(f"- {category}")
    return 0


def _handle_category_remove(args: argparse.Namespace, service: BudgetService) -> int:
    """사용 중이지 않은 카테고리를 삭제한다."""
    category = _category_name(args, "삭제할 카테고리명: ")
    service.remove_category(category)
    print(f"[삭제 완료] category={category.strip()}")
    return 0


def _handle_update(args: argparse.Namespace, service: BudgetService) -> int:
    """거래의 선택 필드를 수정한다."""
    transaction = service.update_transaction(
        args.id,
        date=args.date,
        transaction_type=args.transaction_type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=args.tags,
    )
    print(f"[수정 완료] id={transaction.id}")
    return 0


def _handle_delete(args: argparse.Namespace, service: BudgetService) -> int:
    """거래를 삭제한다."""
    service.delete_transaction(args.id)
    print(f"[삭제 완료] id={args.id}")
    return 0


def _handle_import(args: argparse.Namespace, service: BudgetService) -> int:
    """CSV 파일을 가져온다."""
    result = service.import_csv(args.source)
    print(f"[완료] imported={result.imported}, skipped={result.skipped}")
    for error in result.errors:
        print(f"[건너뜀] {error}")
    return 0


def _handle_export(args: argparse.Namespace, service: BudgetService) -> int:
    """조건에 맞는 거래를 CSV로 내보낸다."""
    count = service.export_csv(
        args.output,
        month=args.month,
        from_date=args.from_date,
        to_date=args.to_date,
    )
    print(f"[완료] {args.output} ({count} records)")
    return 0


def _handle_backup(args: argparse.Namespace, service: BudgetService) -> int:
    """영구 데이터 파일의 ZIP 백업을 만든다."""
    backup_path = service.create_backup(args.out_dir)
    print(f"[백업 완료] {backup_path}")
    return 0


def _handle_recurring_add(args: argparse.Namespace, service: BudgetService) -> int:
    """반복 거래 규칙을 추가한다."""
    rule = service.add_recurring_rule(
        transaction_type=args.transaction_type,
        category=args.category,
        amount=args.amount,
        day=args.day,
        memo=args.memo,
        tags=args.tags,
    )
    print(f"[저장 완료] id={rule.id}")
    return 0


def _handle_recurring_list(args: argparse.Namespace, service: BudgetService) -> int:
    """반복 거래 규칙을 표로 출력한다."""
    del args
    rendered = format_recurring_rules(service.list_recurring_rules())
    print(rendered if rendered else "등록된 반복 규칙이 없습니다.")
    return 0


def _handle_recurring_remove(args: argparse.Namespace, service: BudgetService) -> int:
    """반복 거래 규칙을 삭제한다."""
    service.remove_recurring_rule(args.id)
    print(f"[삭제 완료] id={args.id}")
    return 0


def _handle_recurring_generate(args: argparse.Namespace, service: BudgetService) -> int:
    """특정 월의 반복 거래를 생성한다."""
    created, skipped = service.generate_recurring_transactions(args.month)
    print(f"[완료] created={created}, skipped={skipped}")
    return 0


def build_parser() -> FriendlyArgumentParser:
    """전체 명령과 하위 명령을 포함한 인자 파서를 만든다."""
    parser = FriendlyArgumentParser(description="파일 기반 콘솔 용돈 기입장")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="데이터 저장 폴더 (기본값: ./data)")
    commands = parser.add_subparsers(dest="command", title="commands")

    add_parser = commands.add_parser("add", help="거래를 대화형으로 추가")
    add_parser.set_defaults(handler=_handle_add)

    list_parser = commands.add_parser("list", help="최근 거래 목록 조회")
    list_parser.add_argument("--limit", type=int, default=20, help="조회 개수 (기본값: 20)")
    list_parser.set_defaults(handler=_handle_list)

    search_parser = commands.add_parser("search", help="조건별 거래 검색")
    search_parser.add_argument("--from", dest="from_date", help="시작일 YYYY-MM-DD")
    search_parser.add_argument("--to", dest="to_date", help="종료일 YYYY-MM-DD")
    search_parser.add_argument("--category", help="카테고리")
    search_parser.add_argument("--type", dest="transaction_type", help="income 또는 expense")
    search_parser.add_argument("--q", dest="query", help="메모 검색어")
    search_parser.add_argument("--tag", help="태그")
    search_parser.set_defaults(handler=_handle_search)

    summary_parser = commands.add_parser("summary", help="월별 요약")
    summary_parser.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    summary_parser.add_argument("--top", type=int, default=3, help="지출 카테고리 개수 (기본값: 3)")
    summary_parser.set_defaults(handler=_handle_summary)

    budget_parser = commands.add_parser("budget", help="월 예산 관리")
    budget_commands = budget_parser.add_subparsers(dest="budget_command", required=True)
    budget_set = budget_commands.add_parser("set", help="예산 설정")
    budget_set.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    budget_set.add_argument("--amount", required=True, help="예산 금액")
    budget_set.set_defaults(handler=_handle_budget_set)
    budget_get = budget_commands.add_parser("get", help="예산 조회")
    budget_get.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    budget_get.set_defaults(handler=_handle_budget_get)

    category_parser = commands.add_parser("category", help="카테고리 관리")
    category_commands = category_parser.add_subparsers(dest="category_command", required=True)
    category_add = category_commands.add_parser("add", help="카테고리 추가")
    category_add.add_argument("--name", help="카테고리명 (생략 시 대화형 입력)")
    category_add.set_defaults(handler=_handle_category_add)
    category_list = category_commands.add_parser("list", help="카테고리 목록")
    category_list.set_defaults(handler=_handle_category_list)
    category_remove = category_commands.add_parser("remove", help="카테고리 삭제")
    category_remove.add_argument("--name", help="카테고리명 (생략 시 대화형 입력)")
    category_remove.set_defaults(handler=_handle_category_remove)

    update_parser = commands.add_parser("update", help="ID 기준 거래 수정")
    update_parser.add_argument("--id", required=True, help="거래 ID")
    update_parser.add_argument("--date", help="날짜 YYYY-MM-DD")
    update_parser.add_argument("--type", dest="transaction_type", help="income 또는 expense")
    update_parser.add_argument("--category", help="카테고리")
    update_parser.add_argument("--amount", help="양의 정수 금액")
    update_parser.add_argument("--memo", help="메모 (빈 문자열로 삭제 가능)")
    update_parser.add_argument("--tags", help="쉼표 구분 태그 (빈 문자열로 삭제 가능)")
    update_parser.set_defaults(handler=_handle_update)

    delete_parser = commands.add_parser("delete", help="ID 기준 거래 삭제")
    delete_parser.add_argument("--id", required=True, help="거래 ID")
    delete_parser.set_defaults(handler=_handle_delete)

    import_parser = commands.add_parser("import", help="CSV 거래 가져오기")
    import_parser.add_argument("--from", dest="source", type=Path, required=True, help="가져올 CSV 경로")
    import_parser.set_defaults(handler=_handle_import)

    export_parser = commands.add_parser("export", help="CSV 거래 내보내기")
    export_parser.add_argument("--out", dest="output", type=Path, required=True, help="출력 CSV 경로")
    export_parser.add_argument("--month", help="대상 월 YYYY-MM")
    export_parser.add_argument("--from", dest="from_date", help="시작일 YYYY-MM-DD")
    export_parser.add_argument("--to", dest="to_date", help="종료일 YYYY-MM-DD")
    export_parser.set_defaults(handler=_handle_export)

    backup_parser = commands.add_parser("backup", help="데이터 ZIP 백업")
    backup_parser.add_argument("--out-dir", type=Path, default=Path("backups"), help="백업 폴더")
    backup_parser.set_defaults(handler=_handle_backup)

    recurring_parser = commands.add_parser("recurring", help="반복 거래 관리")
    recurring_commands = recurring_parser.add_subparsers(dest="recurring_command", required=True)
    recurring_add = recurring_commands.add_parser("add", help="반복 거래 규칙 추가")
    recurring_add.add_argument("--type", dest="transaction_type", required=True)
    recurring_add.add_argument("--category", required=True)
    recurring_add.add_argument("--amount", required=True)
    recurring_add.add_argument("--day", required=True, help="매월 생성할 일자 1-31")
    recurring_add.add_argument("--memo", default="")
    recurring_add.add_argument("--tags", default="")
    recurring_add.set_defaults(handler=_handle_recurring_add)
    recurring_list = recurring_commands.add_parser("list", help="반복 거래 규칙 목록")
    recurring_list.set_defaults(handler=_handle_recurring_list)
    recurring_remove = recurring_commands.add_parser("remove", help="반복 거래 규칙 삭제")
    recurring_remove.add_argument("--id", required=True)
    recurring_remove.set_defaults(handler=_handle_recurring_remove)
    recurring_generate = recurring_commands.add_parser("generate", help="특정 월 반복 거래 생성")
    recurring_generate.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    recurring_generate.set_defaults(handler=_handle_recurring_generate)

    return parser


@handle_cli_errors
@log_execution
def run(argv: Sequence[str] | None = None) -> int:
    """CLI 인자를 해석하고 선택된 명령을 실행한다."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0
    service = BudgetService(args.data_dir)
    return args.handler(args, service)


def main(argv: Sequence[str] | None = None) -> int:
    """콘솔 진입점에서 사용할 공개 함수."""
    return run(argv)
