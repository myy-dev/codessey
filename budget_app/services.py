"""거래, 요약, 예산, CSV 및 보너스 기능의 비즈니스 로직."""

from __future__ import annotations

import calendar
import csv
import os
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Generator, Iterable

from .errors import BudgetAppError, ValidationError
from .models import RecurringRule, Transaction
from .repositories import DataStores
from .validators import (
    parse_tags,
    validate_amount,
    validate_category_name,
    validate_date,
    validate_date_range,
    validate_day,
    validate_existing_file,
    validate_month,
    validate_positive_int,
    validate_transaction_type,
)

CSV_COLUMNS = ("date", "type", "category", "amount", "memo", "tags")


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """월별 요약 계산 결과."""

    month: str
    income: int
    expense: int
    balance: int
    top_expenses: tuple[tuple[str, int], ...]
    top_limit: int
    budget: int | None

    @property
    def budget_usage(self) -> float | None:
        """예산이 있으면 지출 사용률을 반환한다."""
        if self.budget is None:
            return None
        return self.expense / self.budget * 100

    @property
    def over_budget(self) -> bool:
        """지출이 설정 예산을 초과했는지 반환한다."""
        return self.budget is not None and self.expense > self.budget


@dataclass(frozen=True, slots=True)
class ImportResult:
    """CSV 가져오기 처리 건수와 건너뛴 행의 이유."""

    imported: int
    skipped: int
    errors: tuple[str, ...]


class BudgetService:
    """파일 저장소 위에서 가계부 기능을 제공한다."""

    def __init__(self, data_dir: Path | str) -> None:
        self.stores = DataStores(Path(data_dir))

    def _require_category(self, category: str) -> str:
        """카테고리 이름과 등록 여부를 검증한다."""
        normalized = validate_category_name(category)
        if not self.stores.categories.contains(normalized):
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {normalized}",
                "category add로 먼저 카테고리를 등록하세요.",
            )
        return normalized

    def _build_transaction(
        self,
        transaction_id: str,
        *,
        date: str | None,
        transaction_type: str | None,
        category: str | None,
        amount: int | str | None,
        memo: str = "",
        tags: str | Iterable[str] | None = None,
    ) -> Transaction:
        """저장하지 않고 검증된 거래 객체를 만든다."""
        return Transaction(
            id=transaction_id,
            type=validate_transaction_type(transaction_type),
            date=validate_date(date),
            amount=validate_amount(amount),
            category=self._require_category(category or ""),
            memo=memo.strip(),
            tags=parse_tags(tags),
        )

    def add_transaction(
        self,
        *,
        date: str,
        transaction_type: str,
        category: str,
        amount: int | str,
        memo: str = "",
        tags: str | Iterable[str] | None = None,
    ) -> Transaction:
        """입력값을 검증하고 새 거래를 저장한다."""
        transaction = self._build_transaction(
            self.stores.transactions.next_id(),
            date=date,
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )
        self.stores.transactions.add(transaction)
        return transaction

    def list_transactions(self, limit: int = 20) -> Generator[Transaction, None, None]:
        """최근 저장된 거래를 제한 개수만큼 스트리밍한다."""
        checked_limit = validate_positive_int(limit, "조회 개수")
        for index, transaction in enumerate(self.stores.transactions.iter_transactions(reverse=True)):
            if index >= checked_limit:
                break
            yield transaction

    def search_transactions(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        category: str | None = None,
        transaction_type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> Generator[Transaction, None, None]:
        """조건과 일치하는 거래를 최신 저장순으로 스트리밍한다."""
        start, end = validate_date_range(from_date, to_date)
        checked_category = self._require_category(category) if category else None
        checked_type = validate_transaction_type(transaction_type) if transaction_type else None
        normalized_query = query.casefold() if query else None
        normalized_tag = tag.strip() if tag else None

        for transaction in self.stores.transactions.iter_transactions(reverse=True):
            if start and transaction.date < start:
                continue
            if end and transaction.date > end:
                continue
            if checked_category and transaction.category != checked_category:
                continue
            if checked_type and transaction.type != checked_type:
                continue
            if normalized_query and normalized_query not in transaction.memo.casefold():
                continue
            if normalized_tag and normalized_tag not in transaction.tags:
                continue
            yield transaction

    def update_transaction(
        self,
        transaction_id: str,
        *,
        date: str | None = None,
        transaction_type: str | None = None,
        category: str | None = None,
        amount: int | str | None = None,
        memo: str | None = None,
        tags: str | Iterable[str] | None = None,
    ) -> Transaction:
        """ID 기준으로 지정된 필드만 수정한다."""
        current = self.stores.transactions.find(transaction_id)
        if current is None:
            raise BudgetAppError(f"거래를 찾을 수 없습니다: {transaction_id}", "list로 ID를 확인하세요.")
        if all(value is None for value in (date, transaction_type, category, amount, memo, tags)):
            raise ValidationError("수정할 필드를 하나 이상 입력해야 합니다.")

        updated = replace(
            current,
            date=validate_date(date) if date is not None else current.date,
            type=(
                validate_transaction_type(transaction_type)
                if transaction_type is not None
                else current.type
            ),
            category=self._require_category(category) if category is not None else current.category,
            amount=validate_amount(amount) if amount is not None else current.amount,
            memo=memo.strip() if memo is not None else current.memo,
            tags=parse_tags(tags) if tags is not None else current.tags,
        )
        if not self.stores.transactions.update(updated):
            raise BudgetAppError(f"거래를 수정하지 못했습니다: {transaction_id}")
        return updated

    def delete_transaction(self, transaction_id: str) -> None:
        """ID 기준으로 거래를 삭제한다."""
        if self.stores.transactions.find(transaction_id) is None:
            raise BudgetAppError(f"거래를 찾을 수 없습니다: {transaction_id}", "list로 ID를 확인하세요.")
        if not self.stores.transactions.delete(transaction_id):
            raise BudgetAppError(f"거래를 삭제하지 못했습니다: {transaction_id}")

    def summarize(self, month: str, top: int = 3) -> SummaryResult:
        """월별 수입, 지출, 잔액과 카테고리별 지출 순위를 계산한다."""
        checked_month = validate_month(month)
        checked_top = validate_positive_int(top, "상위 카테고리 개수")
        income = 0
        expense = 0
        expenses_by_category: Counter[str] = Counter()

        for transaction in self.stores.transactions.iter_transactions():
            if not transaction.date.startswith(f"{checked_month}-"):
                continue
            if transaction.type == "income":
                income += transaction.amount
            else:
                expense += transaction.amount
                expenses_by_category[transaction.category] += transaction.amount

        return SummaryResult(
            month=checked_month,
            income=income,
            expense=expense,
            balance=income - expense,
            top_expenses=tuple(expenses_by_category.most_common(checked_top)),
            top_limit=checked_top,
            budget=self.stores.budgets.get(checked_month),
        )

    def set_budget(self, month: str, amount: int | str) -> int:
        """월 예산을 저장하고 검증된 금액을 반환한다."""
        checked_month = validate_month(month)
        checked_amount = validate_amount(amount)
        self.stores.budgets.set(checked_month, checked_amount)
        return checked_amount

    def get_budget(self, month: str) -> int | None:
        """월 예산을 조회한다."""
        return self.stores.budgets.get(validate_month(month))

    def list_categories(self) -> list[str]:
        """카테고리 목록을 반환한다."""
        return self.stores.categories.list()

    def add_category(self, category: str) -> str:
        """새 카테고리를 추가한다."""
        checked = validate_category_name(category)
        if not self.stores.categories.add(checked):
            raise BudgetAppError(f"이미 등록된 카테고리입니다: {checked}")
        return checked

    def remove_category(self, category: str) -> None:
        """사용 중이지 않은 카테고리를 삭제한다."""
        checked = validate_category_name(category)
        if not self.stores.categories.contains(checked):
            raise BudgetAppError(f"카테고리를 찾을 수 없습니다: {checked}")
        if self.stores.transactions.any_in_category(checked):
            raise BudgetAppError(
                f"거래에서 사용 중인 카테고리는 삭제할 수 없습니다: {checked}",
                "거래의 카테고리를 먼저 수정하거나 삭제하세요.",
            )
        if self.stores.recurring.any_in_category(checked):
            raise BudgetAppError(
                f"반복 규칙에서 사용 중인 카테고리는 삭제할 수 없습니다: {checked}",
                "반복 규칙을 먼저 삭제하세요.",
            )
        if not self.stores.categories.remove(checked):
            raise BudgetAppError(f"카테고리를 삭제하지 못했습니다: {checked}")

    def import_csv(self, source: Path | str) -> ImportResult:
        """CSV 전체를 검증한 뒤 유효한 행을 한 번에 원자적으로 등록한다."""
        source_path = validate_existing_file(Path(source))
        skipped = 0
        errors: list[str] = []
        staged: list[Transaction] = []

        try:
            with source_path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                fieldnames = tuple(reader.fieldnames or ())
                missing = [column for column in CSV_COLUMNS if column not in fieldnames]
                if missing:
                    raise ValidationError(
                        f"CSV 필수 헤더가 없습니다: {', '.join(missing)}",
                        f"필수 헤더: {', '.join(CSV_COLUMNS)}",
                    )
                for row_number, row in enumerate(reader, start=2):
                    try:
                        staged.append(
                            self._build_transaction(
                                "",
                                date=row.get("date"),
                                transaction_type=row.get("type"),
                                category=row.get("category"),
                                amount=row.get("amount"),
                                memo=row.get("memo") or "",
                                tags=row.get("tags") or "",
                            )
                        )
                    except BudgetAppError as exc:
                        skipped += 1
                        errors.append(f"{row_number}행: {exc.message}")
        except (UnicodeError, csv.Error) as exc:
            raise ValidationError(
                "CSV 파일을 UTF-8 형식으로 읽을 수 없습니다.",
                "UTF-8 인코딩과 CSV 따옴표 형식을 확인하세요.",
            ) from exc

        identifiers = self.stores.transactions.reserve_ids(len(staged))
        transactions = tuple(
            replace(transaction, id=transaction_id)
            for transaction, transaction_id in zip(staged, identifiers)
        )
        self.stores.transactions.add_many(transactions)
        return ImportResult(imported=len(transactions), skipped=skipped, errors=tuple(errors))

    def export_csv(
        self,
        output: Path | str,
        *,
        month: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> int:
        """월 또는 기간 조건 거래를 충돌 검사 후 원자적으로 CSV 저장한다."""
        if month and (from_date or to_date):
            raise ValidationError("--month와 --from/--to는 함께 사용할 수 없습니다.")
        if not month and not (from_date and to_date):
            raise ValidationError("--month 또는 --from과 --to를 입력해야 합니다.")

        if month:
            checked_month = validate_month(month)
            year, month_number = (int(part) for part in checked_month.split("-"))
            last_day = calendar.monthrange(year, month_number)[1]
            start = f"{checked_month}-01"
            end = f"{checked_month}-{last_day:02d}"
        else:
            start, end = validate_date_range(from_date, to_date)

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_output = output_path.resolve()
        for data_path in self.stores.paths():
            try:
                same_file = output_path.exists() and output_path.samefile(data_path)
            except OSError:
                same_file = False
            if same_file or resolved_output == data_path.resolve():
                raise ValidationError(
                    f"내보내기 경로가 저장 파일과 충돌합니다: {output_path}",
                    "data 폴더 밖의 CSV 경로를 지정하세요.",
                )

        count = 0
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=output_path.parent,
                prefix=f".{output_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                writer = csv.DictWriter(temp_file, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                for transaction in self.search_transactions(from_date=start, to_date=end):
                    writer.writerow(
                        {
                            "date": transaction.date,
                            "type": transaction.type,
                            "category": transaction.category,
                            "amount": transaction.amount,
                            "memo": transaction.memo,
                            "tags": ",".join(transaction.tags),
                        }
                    )
                    count += 1
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, output_path)
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise
        return count

    def create_backup(self, output_dir: Path | str = "backups") -> Path:
        """모든 영구 데이터 파일을 타임스탬프 ZIP으로 백업한다."""
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = target_dir / f"budget-backup-{timestamp}.zip"
        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for data_path in self.stores.paths():
                archive.write(data_path, arcname=data_path.name)
        return backup_path

    def add_recurring_rule(
        self,
        *,
        transaction_type: str,
        category: str,
        amount: int | str,
        day: int | str,
        memo: str = "",
        tags: str | Iterable[str] | None = None,
    ) -> RecurringRule:
        """매월 적용할 반복 거래 규칙을 저장한다."""
        rule = RecurringRule(
            id=self.stores.recurring.next_id(),
            type=validate_transaction_type(transaction_type),
            category=self._require_category(category),
            amount=validate_amount(amount),
            day=validate_day(day),
            memo=memo.strip(),
            tags=parse_tags(tags),
        )
        self.stores.recurring.add(rule)
        return rule

    def list_recurring_rules(self) -> list[RecurringRule]:
        """등록된 반복 규칙 목록을 반환한다."""
        return list(self.stores.recurring.iter_rules())

    def remove_recurring_rule(self, rule_id: str) -> None:
        """ID 기준으로 반복 규칙을 삭제한다."""
        if not self.stores.recurring.delete(rule_id):
            raise BudgetAppError(f"반복 규칙을 찾을 수 없습니다: {rule_id}")

    def generate_recurring_transactions(self, month: str) -> tuple[int, int]:
        """반복 규칙을 특정 월의 거래로 만들고 중복 생성을 건너뛴다."""
        checked_month = validate_month(month)
        year, month_number = (int(part) for part in checked_month.split("-"))
        last_day = calendar.monthrange(year, month_number)[1]
        existing_tags = {
            tag
            for transaction in self.stores.transactions.iter_transactions()
            for tag in transaction.tags
            if tag.startswith("recurring:")
        }
        created = 0
        skipped = 0

        for rule in self.stores.recurring.iter_rules():
            marker = f"recurring:{rule.id}:{checked_month}"
            if marker in existing_tags:
                skipped += 1
                continue
            day = min(rule.day, last_day)
            self.add_transaction(
                date=f"{checked_month}-{day:02d}",
                transaction_type=rule.type,
                category=rule.category,
                amount=rule.amount,
                memo=rule.memo,
                tags=(*rule.tags, marker),
            )
            existing_tags.add(marker)
            created += 1
        return created, skipped
