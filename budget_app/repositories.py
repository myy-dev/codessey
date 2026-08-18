"""JSONL 파일 저장소와 원자적 파일 교체 구현."""

from __future__ import annotations

import json
import heapq
import os
import tempfile
from pathlib import Path
from typing import Any, Generator, Iterable

from .errors import DataFileError
from .models import RecurringRule, Transaction

DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "etc")


def _transaction_sort_key(transaction: Transaction) -> tuple[str, str]:
    """거래를 날짜와 ID 오름차순으로 저장하기 위한 키를 반환한다."""
    return transaction.date, transaction.id


def _identifier_number(value: object, prefix: str) -> int:
    """TX-000001 같은 ID에서 숫자를 읽고 형식이 다르면 0을 반환한다."""
    if not isinstance(value, str) or not value.startswith(f"{prefix}-"):
        return 0
    try:
        return int(value[len(prefix) + 1 :])
    except ValueError:
        return 0


def _ensure_file(path: Path) -> None:
    """부모 폴더와 빈 저장 파일을 만든다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


def _decode_json_line(line: str, path: Path) -> dict[str, Any]:
    """JSONL 한 줄을 객체로 해석하고 읽기 쉬운 오류를 만든다."""
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise DataFileError(
            f"저장 파일의 JSON 형식이 손상되었습니다: {path}",
            "백업 파일을 복원하거나 손상된 줄을 수정하세요.",
        ) from exc
    if not isinstance(value, dict):
        raise DataFileError(f"저장 파일의 항목이 객체가 아닙니다: {path}")
    return value


def _iter_lines_reverse(path: Path, block_size: int = 8192) -> Generator[str, None, None]:
    """파일을 전부 메모리에 올리지 않고 마지막 줄부터 읽는다."""
    with path.open("rb") as file:
        file.seek(0, os.SEEK_END)
        position = file.tell()
        buffer = b""
        while position > 0:
            read_size = min(block_size, position)
            position -= read_size
            file.seek(position)
            buffer = file.read(read_size) + buffer
            lines = buffer.split(b"\n")
            buffer = lines[0]
            for raw_line in reversed(lines[1:]):
                if raw_line.strip():
                    yield raw_line.decode("utf-8")
        if buffer.strip():
            yield buffer.decode("utf-8")


def _iter_json_objects(path: Path, reverse: bool = False) -> Generator[dict[str, Any], None, None]:
    """JSONL 항목을 정방향 또는 역방향으로 스트리밍한다."""
    _ensure_file(path)
    if reverse:
        for line in _iter_lines_reverse(path):
            yield _decode_json_line(line, path)
        return

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield _decode_json_line(line, path)


def _append_json(path: Path, data: dict[str, Any]) -> None:
    """JSON 객체 하나를 파일 마지막에 추가한다."""
    _ensure_file(path)
    with path.open("a", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, separators=(",", ":"))
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


def _atomic_write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """임시 파일을 완전히 쓴 뒤 원본 경로로 원자적으로 교체한다."""
    _ensure_file(path)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            for record in records:
                json.dump(record, temp_file, ensure_ascii=False, separators=(",", ":"))
                temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise


class SequenceStore:
    """삭제 후에도 재사용되지 않는 영구 ID 시퀀스 저장소."""

    _PREFIXES = {"transaction": "TX", "recurring": "RC"}

    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "sequences.jsonl"
        _ensure_file(self.path)
        if self.path.stat().st_size == 0:
            transaction_max = 0
            recurring_max = 0
            for data in _iter_json_objects(data_dir / "transactions.jsonl"):
                transaction_max = max(transaction_max, _identifier_number(data.get("id"), "TX"))
                raw_tags = data.get("tags", [])
                tags = raw_tags.split(",") if isinstance(raw_tags, str) else raw_tags
                if isinstance(tags, list):
                    for tag in tags:
                        if isinstance(tag, str) and tag.startswith("recurring:RC-"):
                            parts = tag.split(":")
                            if len(parts) >= 2:
                                recurring_max = max(
                                    recurring_max,
                                    _identifier_number(parts[1], "RC"),
                                )
            for data in _iter_json_objects(data_dir / "recurring.jsonl"):
                recurring_max = max(recurring_max, _identifier_number(data.get("id"), "RC"))
            _atomic_write_jsonl(
                self.path,
                (
                    {"name": "transaction", "value": transaction_max},
                    {"name": "recurring", "value": recurring_max},
                ),
            )

    def reserve(self, name: str, count: int = 1) -> tuple[str, ...]:
        """지정한 개수의 연속 ID를 예약하고 마지막 값을 영구 저장한다."""
        if name not in self._PREFIXES:
            raise DataFileError(f"알 수 없는 ID 시퀀스입니다: {name}")
        if count <= 0:
            return ()

        values: dict[str, int] = {}
        for data in _iter_json_objects(self.path):
            sequence_name = data.get("name")
            try:
                sequence_value = int(data["value"])
            except (KeyError, TypeError, ValueError) as exc:
                raise DataFileError(f"ID 시퀀스 데이터 형식이 올바르지 않습니다: {self.path}") from exc
            if isinstance(sequence_name, str):
                values[sequence_name] = sequence_value

        current = values.get(name, 0)
        values[name] = current + count
        _atomic_write_jsonl(
            self.path,
            ({"name": key, "value": values.get(key, 0)} for key in self._PREFIXES),
        )
        prefix = self._PREFIXES[name]
        return tuple(f"{prefix}-{number:06d}" for number in range(current + 1, current + count + 1))


class TransactionRepository:
    """거래 JSONL 파일에 대한 스트리밍 CRUD 저장소."""

    def __init__(self, data_dir: Path, sequences: SequenceStore | None = None) -> None:
        self.path = data_dir / "transactions.jsonl"
        self.sequences = sequences or SequenceStore(data_dir)
        _ensure_file(self.path)

    def iter_transactions(self, reverse: bool = False) -> Generator[Transaction, None, None]:
        """거래를 한 건씩 읽는다. reverse=True이면 최신 저장 건부터 읽는다."""
        for data in _iter_json_objects(self.path, reverse=reverse):
            try:
                yield Transaction.from_dict(data)
            except (KeyError, TypeError, ValueError) as exc:
                raise DataFileError(f"거래 데이터 형식이 올바르지 않습니다: {self.path}") from exc

    def next_id(self) -> str:
        """삭제 후에도 재사용되지 않는 다음 거래 ID를 만든다."""
        return self.sequences.reserve("transaction")[0]

    def reserve_ids(self, count: int) -> tuple[str, ...]:
        """CSV 일괄 등록에 사용할 거래 ID 여러 개를 예약한다."""
        return self.sequences.reserve("transaction", count)

    def add(self, transaction: Transaction) -> None:
        """거래 한 건을 날짜순 위치에 원자적으로 추가한다."""
        self.add_many((transaction,))

    def add_many(self, transactions: Iterable[Transaction]) -> None:
        """거래 묶음을 기존 날짜순 스트림과 병합해 원자적으로 저장한다."""
        incoming = sorted(transactions, key=_transaction_sort_key)
        if not incoming:
            return
        merged = heapq.merge(
            self.iter_transactions(),
            iter(incoming),
            key=_transaction_sort_key,
        )
        _atomic_write_jsonl(self.path, (transaction.to_dict() for transaction in merged))

    def find(self, transaction_id: str) -> Transaction | None:
        """ID가 일치하는 거래를 찾는다."""
        return next(
            (item for item in self.iter_transactions() if item.id == transaction_id),
            None,
        )

    def update(self, transaction: Transaction) -> bool:
        """ID가 같은 거래를 교체하고 날짜순으로 원자적 재정렬한다."""
        if self.find(transaction.id) is None:
            return False

        def remaining() -> Generator[Transaction, None, None]:
            for current in self.iter_transactions():
                if current.id != transaction.id:
                    yield current

        merged = heapq.merge(remaining(), iter((transaction,)), key=_transaction_sort_key)
        _atomic_write_jsonl(self.path, (current.to_dict() for current in merged))
        return True

    def delete(self, transaction_id: str) -> bool:
        """ID가 같은 거래를 제외하고 전체 파일을 원자적으로 저장한다."""
        found = False

        def records() -> Generator[dict[str, Any], None, None]:
            nonlocal found
            for current in self.iter_transactions():
                if current.id == transaction_id:
                    found = True
                    continue
                yield current.to_dict()

        _atomic_write_jsonl(self.path, records())
        return found

    def any_in_category(self, category: str) -> bool:
        """특정 카테고리를 사용하는 거래가 있는지 스트리밍해 확인한다."""
        return any(item.category == category for item in self.iter_transactions())


class CategoryStore:
    """카테고리 목록 저장소."""

    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "categories.jsonl"
        _ensure_file(self.path)
        if self.path.stat().st_size == 0:
            _atomic_write_jsonl(self.path, ({"name": name} for name in DEFAULT_CATEGORIES))

    def iter_categories(self) -> Generator[str, None, None]:
        """카테고리를 저장 순서대로 스트리밍한다."""
        for data in _iter_json_objects(self.path):
            name = data.get("name")
            if not isinstance(name, str) or not name:
                raise DataFileError(f"카테고리 데이터 형식이 올바르지 않습니다: {self.path}")
            yield name

    def list(self) -> list[str]:
        """정렬된 카테고리 목록을 반환한다."""
        return sorted(self.iter_categories())

    def contains(self, category: str) -> bool:
        """카테고리 등록 여부를 확인한다."""
        return any(name == category for name in self.iter_categories())

    def add(self, category: str) -> bool:
        """중복이 아닐 때 카테고리를 추가한다."""
        if self.contains(category):
            return False
        _append_json(self.path, {"name": category})
        return True

    def remove(self, category: str) -> bool:
        """카테고리를 제외하고 파일을 원자적으로 저장한다."""
        found = False

        def records() -> Generator[dict[str, str], None, None]:
            nonlocal found
            for current in self.iter_categories():
                if current == category:
                    found = True
                    continue
                yield {"name": current}

        _atomic_write_jsonl(self.path, records())
        return found


class BudgetStore:
    """월별 예산 저장소."""

    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "budgets.jsonl"
        _ensure_file(self.path)

    def get(self, month: str) -> int | None:
        """월에 설정된 예산을 반환한다."""
        for data in _iter_json_objects(self.path):
            if data.get("month") == month:
                try:
                    return int(data["amount"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise DataFileError(f"예산 데이터 형식이 올바르지 않습니다: {self.path}") from exc
        return None

    def set(self, month: str, amount: int) -> None:
        """월별 예산을 추가하거나 교체하고 원자적으로 저장한다."""
        found = False

        def records() -> Generator[dict[str, Any], None, None]:
            nonlocal found
            for data in _iter_json_objects(self.path):
                if data.get("month") == month:
                    found = True
                    yield {"month": month, "amount": amount}
                else:
                    yield data
            if not found:
                yield {"month": month, "amount": amount}

        _atomic_write_jsonl(self.path, records())


class RecurringRepository:
    """반복 거래 규칙 저장소."""

    def __init__(self, data_dir: Path, sequences: SequenceStore | None = None) -> None:
        self.path = data_dir / "recurring.jsonl"
        self.sequences = sequences or SequenceStore(data_dir)
        _ensure_file(self.path)

    def iter_rules(self) -> Generator[RecurringRule, None, None]:
        """반복 규칙을 한 건씩 읽는다."""
        for data in _iter_json_objects(self.path):
            try:
                yield RecurringRule.from_dict(data)
            except (KeyError, TypeError, ValueError) as exc:
                raise DataFileError(f"반복 규칙 데이터 형식이 올바르지 않습니다: {self.path}") from exc

    def next_id(self) -> str:
        """삭제 후에도 재사용되지 않는 다음 반복 규칙 ID를 만든다."""
        return self.sequences.reserve("recurring")[0]

    def add(self, rule: RecurringRule) -> None:
        """반복 규칙을 추가한다."""
        _append_json(self.path, rule.to_dict())

    def delete(self, rule_id: str) -> bool:
        """ID가 같은 반복 규칙을 원자적으로 삭제한다."""
        found = False

        def records() -> Generator[dict[str, Any], None, None]:
            nonlocal found
            for rule in self.iter_rules():
                if rule.id == rule_id:
                    found = True
                    continue
                yield rule.to_dict()

        _atomic_write_jsonl(self.path, records())
        return found

    def any_in_category(self, category: str) -> bool:
        """카테고리를 사용하는 반복 규칙이 있는지 확인한다."""
        return any(rule.category == category for rule in self.iter_rules())


class DataStores:
    """CLI 실행에서 함께 사용하는 모든 파일 저장소를 묶는다."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sequences = SequenceStore(data_dir)
        self.transactions = TransactionRepository(data_dir, self.sequences)
        self.categories = CategoryStore(data_dir)
        self.budgets = BudgetStore(data_dir)
        self.recurring = RecurringRepository(data_dir, self.sequences)

    def paths(self) -> tuple[Path, ...]:
        """백업할 모든 영구 저장 파일 경로를 반환한다."""
        return (
            self.transactions.path,
            self.categories.path,
            self.budgets.path,
            self.recurring.path,
            self.sequences.path,
        )
