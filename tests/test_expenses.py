from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from database import connect, migrate  # noqa: E402
from expenses import (  # noqa: E402
    ValidationError,
    create_expense,
    delete_expense,
    list_expenses,
    parse_money,
    summarize_by_category,
)


class ExpensesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "expenses.db"
        self.connection = connect(database_path)
        migrate(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        self.temp_dir.cleanup()

    def test_parse_money_accepts_common_formats(self) -> None:
        self.assertEqual(parse_money("120.50"), 12050)
        self.assertEqual(parse_money("120,50"), 12050)
        self.assertEqual(parse_money("1.250,75"), 125075)

    def test_create_and_list_expenses(self) -> None:
        expense = create_expense(
            self.connection,
            {
                "description": "Hospedagem",
                "category": "tecnologia",
                "amount": "120.50",
                "expense_date": "2026-08-26",
                "payment_method": "cartao",
            },
        )

        records = list_expenses(self.connection)

        self.assertEqual(expense["id"], 1)
        self.assertEqual(expense["category"], "Tecnologia")
        self.assertEqual(expense["amount"], "120.50")
        self.assertEqual(len(records), 1)

    def test_filters_and_summary(self) -> None:
        create_expense(
            self.connection,
            {
                "description": "Hospedagem",
                "category": "tecnologia",
                "amount": "120.50",
                "expense_date": "2026-08-26",
                "payment_method": "cartao",
            },
        )
        create_expense(
            self.connection,
            {
                "description": "Almoço",
                "category": "alimentacao",
                "amount": "45.00",
                "expense_date": "2026-08-25",
                "payment_method": "pix",
            },
        )

        filtered = list_expenses(self.connection, category="Tecnologia")
        summary = summarize_by_category(self.connection)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["description"], "Hospedagem")
        self.assertEqual(summary[0]["category"], "Tecnologia")
        self.assertEqual(summary[0]["total_amount"], "120.50")

    def test_validation_rejects_invalid_payload(self) -> None:
        with self.assertRaises(ValidationError):
            create_expense(
                self.connection,
                {
                    "description": "",
                    "category": "tecnologia",
                    "amount": "abc",
                    "expense_date": "26/08/2026",
                    "payment_method": "cartao",
                },
            )

    def test_delete_expense(self) -> None:
        expense = create_expense(
            self.connection,
            {
                "description": "Licença",
                "category": "software",
                "amount": "89.90",
                "expense_date": "2026-08-24",
                "payment_method": "boleto",
            },
        )

        self.assertTrue(delete_expense(self.connection, int(expense["id"])))
        self.assertEqual(list_expenses(self.connection), [])


if __name__ == "__main__":
    unittest.main()
