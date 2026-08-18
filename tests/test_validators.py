"""입력 검증 함수 테스트."""

from __future__ import annotations

import unittest

from budget_app.errors import ValidationError
from budget_app.validators import (
    parse_tags,
    validate_amount,
    validate_date,
    validate_date_range,
    validate_month,
    validate_transaction_type,
)


class ValidatorTests(unittest.TestCase):
    """날짜, 금액, 타입, 태그 검증을 확인한다."""

    def test_valid_values_are_normalized(self) -> None:
        self.assertEqual(validate_date("2024-02-29"), "2024-02-29")
        self.assertEqual(validate_month("2024-02"), "2024-02")
        self.assertEqual(validate_amount("15000"), 15000)
        self.assertEqual(validate_transaction_type(" Expense "), "expense")
        self.assertEqual(parse_tags("meal, daily,meal"), ("meal", "daily"))

    def test_invalid_values_raise_readable_errors(self) -> None:
        invalid_calls = (
            lambda: validate_date("2024-13-40"),
            lambda: validate_month("2024-13"),
            lambda: validate_amount(0),
            lambda: validate_amount(-1),
            lambda: validate_transaction_type("transfer"),
            lambda: validate_date_range("2024-02-01", "2024-01-01"),
        )
        for call in invalid_calls:
            with self.subTest(call=call), self.assertRaises(ValidationError):
                call()


if __name__ == "__main__":
    unittest.main()
