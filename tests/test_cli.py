"""CLI 진입점과 사용자 출력 테스트"""

from __future__ import annotations

import csv
import io
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from budget_app.cli import run
from budget_app.formatters import iter_transaction_lines
from budget_app.models import Transaction


class CliTests(unittest.TestCase):
    """종료 코드·대화형 입력·오류 출력 형식 검증"""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.data_dir = Path(self.temp_directory.name) / "data"

    def _run(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        argv = ["--data-dir", str(self.data_dir), *arguments]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = run(argv)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_category_list_initializes_data_and_returns_zero(self) -> None:
        exit_code, stdout, stderr = self._run("category", "list")
        self.assertEqual(exit_code, 0)
        self.assertIn("- food", stdout)
        self.assertEqual(stderr, "")

    def test_interactive_add_reprompts_invalid_values(self) -> None:
        responses = iter(
            (
                "2024-13-40",
                "2024-01-15",
                "wrong",
                "expense",
                "missing",
                "food",
                "0",
                "15000",
                "점심",
                "meal",
            )
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("builtins.input", side_effect=lambda _prompt: next(responses)):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = run(["--data-dir", str(self.data_dir), "add"])
        self.assertEqual(exit_code, 0)
        self.assertIn("[오류]", stdout.getvalue())
        self.assertIn("[저장 완료] id=TX-000001", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_expected_errors_have_nonzero_code_without_traceback(self) -> None:
        exit_code, _stdout, stderr = self._run("delete", "--id", "TX-999999")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("[오류] 거래를 찾을 수 없습니다", stderr)
        self.assertIn("[힌트]", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_keyboard_interrupt_returns_130_without_traceback(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = run(["--data-dir", str(self.data_dir), "add"])
        self.assertEqual(exit_code, 130)
        self.assertIn("[취소]", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_invalid_export_filter_returns_nonzero(self) -> None:
        output = Path(self.temp_directory.name) / "out.csv"
        exit_code, _stdout, stderr = self._run("export", "--out", str(output))
        self.assertEqual(exit_code, 2)
        self.assertIn("--month 또는 --from과 --to", stderr)

    def test_budget_and_summary_output(self) -> None:
        exit_code, stdout, _stderr = self._run(
            "budget",
            "set",
            "--month",
            "2024-01",
            "--amount",
            "500000",
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("500,000원", stdout)
        exit_code, stdout, _stderr = self._run("summary", "--month", "2024-01")
        self.assertEqual(exit_code, 0)
        self.assertIn("데이터 없음", stdout)
        self.assertIn("사용률 0.0%", stdout)

    def test_import_command_reports_counts_and_list_renders_table(self) -> None:
        source = Path(self.temp_directory.name) / "import.csv"
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
                    "tags": "meal",
                }
            )
        exit_code, stdout, stderr = self._run("import", "--from", str(source))
        self.assertEqual(exit_code, 0)
        self.assertIn("imported=1, skipped=0", stdout)
        self.assertEqual(stderr, "")

        exit_code, stdout, stderr = self._run("list")
        self.assertEqual(exit_code, 0)
        self.assertIn("ID", stdout)
        self.assertIn("TX-000001", stdout)
        self.assertIn("점심", stdout)
        self.assertEqual(stderr, "")

    def test_transaction_table_consumes_source_lazily(self) -> None:
        consumed: list[str] = []

        def transactions() -> Iterator[Transaction]:
            for identifier in ("TX-000001", "TX-000002"):
                consumed.append(identifier)
                yield Transaction(
                    id=identifier,
                    type="expense",
                    date="2024-01-01",
                    amount=100,
                    category="food",
                )

        lines = iter(iter_transaction_lines(transactions()))
        self.assertIn("ID", next(lines))
        self.assertEqual(consumed, ["TX-000001"])
        next(lines)
        next(lines)
        self.assertEqual(consumed, ["TX-000001"])
        next(lines)
        self.assertEqual(consumed, ["TX-000001", "TX-000002"])


if __name__ == "__main__":
    unittest.main()
