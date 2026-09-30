"""저장소와 서비스 통합 테스트"""

from __future__ import annotations

import csv
import inspect
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from budget_app.errors import BudgetAppError, ValidationError
from budget_app.repositories import TransactionRepository
from budget_app.services import BudgetService


class BudgetServiceTests(unittest.TestCase):
    """필수·보너스 기능의 파일 영속성 검증"""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.root = Path(self.temp_directory.name)
        self.data_dir = self.root / "data"
        self.service = BudgetService(self.data_dir)

    def _add_sample_transactions(self) -> tuple[str, str, str]:
        first = self.service.add_transaction(
            date="2024-01-12",
            transaction_type="expense",
            category="transport",
            amount=20000,
            memo="버스 충전",
            tags="commute",
        )
        second = self.service.add_transaction(
            date="2024-01-14",
            transaction_type="income",
            category="salary",
            amount=3000000,
            memo="월급",
            tags="monthly,salary",
        )
        third = self.service.add_transaction(
            date="2024-01-15",
            transaction_type="expense",
            category="food",
            amount=15000,
            memo="점심",
            tags="meal",
        )
        return first.id, second.id, third.id

    def test_initializes_five_persistent_jsonl_files_and_default_categories(self) -> None:
        expected = {
            "transactions.jsonl",
            "categories.jsonl",
            "budgets.jsonl",
            "recurring.jsonl",
            "sequences.jsonl",
        }
        self.assertEqual({path.name for path in self.data_dir.iterdir()}, expected)
        self.assertEqual(
            set(self.service.list_categories()),
            {"food", "transport", "rent", "salary", "etc"},
        )

    def test_crud_list_and_search_use_latest_date_order(self) -> None:
        first_id, _, third_id = self._add_sample_transactions()
        self.assertTrue(inspect.isgeneratorfunction(TransactionRepository.iter_transactions))
        self.assertTrue(inspect.isgeneratorfunction(self.service.list_transactions))
        self.assertTrue(inspect.isgeneratorfunction(self.service.search_transactions))

        listed = list(self.service.list_transactions(limit=2))
        self.assertEqual([item.id for item in listed], [third_id, "TX-000002"])

        searched = list(
            self.service.search_transactions(
                from_date="2024-01-01",
                to_date="2024-01-31",
                transaction_type="expense",
                query="점심",
                tag="meal",
            )
        )
        self.assertEqual([item.id for item in searched], [third_id])

        all_expenses = list(self.service.search_transactions(transaction_type="expense"))
        self.assertEqual([item.id for item in all_expenses], [third_id, first_id])

        with patch("budget_app.repositories.os.replace", wraps=os.replace) as replace_mock:
            updated = self.service.update_transaction(
                first_id,
                date="2024-01-13",
                transaction_type="income",
                category="food",
                amount=25000,
                memo="교통과 간식",
                tags="changed,test",
            )
        replace_mock.assert_called_once()
        self.assertEqual(updated.type, "income")
        self.assertEqual(updated.amount, 25000)
        self.assertEqual(updated.tags, ("changed", "test"))
        self.assertFalse(any(self.data_dir.glob(".*.tmp")))

        self.service.delete_transaction(third_id)
        self.assertIsNone(self.service.stores.transactions.find(third_id))
        self.assertFalse(any(self.data_dir.glob(".*.tmp")))

    def test_out_of_order_add_and_date_update_stay_latest_first(self) -> None:
        newest = self.service.add_transaction(
            date="2024-12-31",
            transaction_type="expense",
            category="food",
            amount=100,
        )
        older = self.service.add_transaction(
            date="2024-01-01",
            transaction_type="expense",
            category="food",
            amount=200,
        )
        self.assertEqual(
            [item.id for item in self.service.list_transactions()],
            [newest.id, older.id],
        )
        self.assertEqual(
            [item.id for item in self.service.search_transactions(transaction_type="expense")],
            [newest.id, older.id],
        )

        self.service.update_transaction(older.id, date="2025-01-01")
        self.assertEqual(
            [item.id for item in self.service.list_transactions()],
            [older.id, newest.id],
        )

    def test_missing_ids_and_invalid_updates_are_reported(self) -> None:
        with self.assertRaises(BudgetAppError):
            self.service.update_transaction("TX-999999", memo="없음")
        with self.assertRaises(BudgetAppError):
            self.service.delete_transaction("TX-999999")

        transaction = self.service.add_transaction(
            date="2024-01-01",
            transaction_type="expense",
            category="food",
            amount=1,
        )
        with self.assertRaises(ValidationError):
            self.service.update_transaction(transaction.id)

    def test_summary_budget_usage_and_over_budget_warning_state(self) -> None:
        self._add_sample_transactions()
        self.service.set_budget("2024-01", 30000)
        summary = self.service.summarize("2024-01", top=2)
        self.assertEqual(summary.income, 3000000)
        self.assertEqual(summary.expense, 35000)
        self.assertEqual(summary.balance, 2965000)
        self.assertEqual(summary.top_expenses, (("transport", 20000), ("food", 15000)))
        self.assertAlmostEqual(summary.budget_usage or 0, 116.666, places=2)
        self.assertTrue(summary.over_budget)

        empty = self.service.summarize("2024-02")
        self.assertEqual((empty.income, empty.expense), (0, 0))

    def test_category_lifecycle_and_in_use_protection(self) -> None:
        self.assertEqual(self.service.add_category("hobby"), "hobby")
        self.assertIn("hobby", self.service.list_categories())
        self.service.remove_category("hobby")
        self.assertNotIn("hobby", self.service.list_categories())

        self.service.add_transaction(
            date="2024-01-01",
            transaction_type="expense",
            category="food",
            amount=1000,
        )
        with self.assertRaises(BudgetAppError):
            self.service.remove_category("food")

    def test_csv_import_export_schema_counts_and_filters(self) -> None:
        source = self.root / "import.csv"
        with source.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=("date", "type", "category", "amount", "memo", "tags"),
            )
            writer.writeheader()
            writer.writerow(
                {
                    "date": "2024-01-15",
                    "type": "expense",
                    "category": "food",
                    "amount": "15000",
                    "memo": "점심",
                    "tags": "meal,daily",
                }
            )
            writer.writerow(
                {
                    "date": "2024-99-99",
                    "type": "expense",
                    "category": "food",
                    "amount": "1",
                    "memo": "잘못된 행",
                    "tags": "",
                }
            )

        result = self.service.import_csv(source)
        self.assertEqual((result.imported, result.skipped), (1, 1))
        output = self.root / "export.csv"
        self.assertEqual(self.service.export_csv(output, month="2024-01"), 1)
        with output.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(tuple(rows[0]), ("date", "type", "category", "amount", "memo", "tags"))
        self.assertEqual(rows[0]["tags"], "meal,daily")

        range_output = self.root / "range.csv"
        self.assertEqual(
            self.service.export_csv(
                range_output,
                from_date="2024-01-01",
                to_date="2024-01-31",
            ),
            1,
        )
        with self.assertRaises(ValidationError):
            self.service.export_csv(self.root / "invalid.csv")

    def test_import_skips_incomplete_rows_without_partial_failure(self) -> None:
        source = self.root / "incomplete.csv"
        source.write_text(
            "date,type,category,amount,memo,tags\n"
            "2024-01-01,expense,food,10,정상,x\n"
            "2024-01-02\n",
            encoding="utf-8",
        )
        result = self.service.import_csv(source)
        self.assertEqual((result.imported, result.skipped), (1, 1))
        self.assertIn("거래 타입은 비어 있을 수 없습니다", result.errors[0])
        self.assertEqual(len(list(self.service.list_transactions())), 1)

        invalid_utf8 = self.root / "invalid-utf8.csv"
        invalid_utf8.write_bytes(
            b"date,type,category,amount,memo,tags\n2024-01-02,expense,food,20,\xff,x\n"
        )
        with self.assertRaises(ValidationError):
            self.service.import_csv(invalid_utf8)
        self.assertEqual(len(list(self.service.list_transactions())), 1)

        additional = self.root / "additional.csv"
        additional.write_text(
            "date,type,category,amount,memo,tags\n"
            "2024-01-03,expense,food,30,추가,y\n",
            encoding="utf-8",
        )
        transactions_path = self.service.stores.transactions.path
        original_transactions = transactions_path.read_bytes()
        real_replace = os.replace

        def fail_transaction_replace(
            source_path: str | os.PathLike[str],
            destination_path: str | os.PathLike[str],
        ) -> None:
            if Path(destination_path) == transactions_path:
                raise OSError("거래 파일 교체 실패")
            real_replace(source_path, destination_path)

        with patch("budget_app.repositories.os.replace", side_effect=fail_transaction_replace):
            with self.assertRaises(OSError):
                self.service.import_csv(additional)
        self.assertEqual(transactions_path.read_bytes(), original_transactions)
        self.assertFalse(any(self.data_dir.glob(".*.tmp")))

    def test_export_rejects_data_file_collision_and_preserves_existing_output(self) -> None:
        self.service.add_transaction(
            date="2024-01-01",
            transaction_type="expense",
            category="food",
            amount=100,
        )
        transactions_path = self.service.stores.transactions.path
        original_transactions = transactions_path.read_bytes()
        with self.assertRaises(ValidationError):
            self.service.export_csv(transactions_path, month="2024-01")
        self.assertEqual(transactions_path.read_bytes(), original_transactions)

        symlink_path = self.root / "transactions-link.csv"
        symlink_path.symlink_to(transactions_path)
        with self.assertRaises(ValidationError):
            self.service.export_csv(symlink_path, month="2024-01")
        self.assertEqual(transactions_path.read_bytes(), original_transactions)

        output = self.root / "existing.csv"
        output.write_text("기존 내용", encoding="utf-8")
        with patch("budget_app.services.os.replace", side_effect=OSError("교체 실패")):
            with self.assertRaises(OSError):
                self.service.export_csv(output, month="2024-01")
        self.assertEqual(output.read_text(encoding="utf-8"), "기존 내용")
        self.assertFalse(any(self.root.glob(".existing.csv.*.tmp")))

    def test_deleted_transaction_ids_are_not_reused(self) -> None:
        first = self.service.add_transaction(
            date="2024-01-01",
            transaction_type="expense",
            category="food",
            amount=1,
        )
        self.service.delete_transaction(first.id)
        second = self.service.add_transaction(
            date="2024-01-02",
            transaction_type="expense",
            category="food",
            amount=2,
        )
        self.assertEqual((first.id, second.id), ("TX-000001", "TX-000002"))

    def test_backup_contains_all_data_files(self) -> None:
        backup = self.service.create_backup(self.root / "backups")
        self.assertRegex(backup.name, r"^budget-backup-\d{8}-\d{6}-\d{6}\.zip$")
        with zipfile.ZipFile(backup) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    "transactions.jsonl",
                    "categories.jsonl",
                    "budgets.jsonl",
                    "recurring.jsonl",
                    "sequences.jsonl",
                },
            )

    def test_recurring_rules_generate_once_per_month_and_clamp_day(self) -> None:
        rule = self.service.add_recurring_rule(
            transaction_type="expense",
            category="rent",
            amount=500000,
            day=31,
            memo="월세",
            tags="fixed",
        )
        self.assertEqual(rule.id, "RC-000001")
        self.assertEqual(self.service.generate_recurring_transactions("2024-02"), (1, 0))
        self.assertEqual(self.service.generate_recurring_transactions("2024-02"), (0, 1))
        generated = list(self.service.list_transactions())
        self.assertEqual(generated[0].date, "2024-02-29")
        self.assertIn("recurring:RC-000001:2024-02", generated[0].tags)

        with self.assertRaises(BudgetAppError):
            self.service.remove_category("rent")
        self.service.remove_recurring_rule(rule.id)
        self.assertEqual(self.service.list_recurring_rules(), [])

        replacement = self.service.add_recurring_rule(
            transaction_type="expense",
            category="rent",
            amount=600000,
            day=1,
            memo="새 월세",
        )
        self.assertEqual(replacement.id, "RC-000002")
        self.assertEqual(self.service.generate_recurring_transactions("2024-02"), (1, 0))


if __name__ == "__main__":
    unittest.main()
