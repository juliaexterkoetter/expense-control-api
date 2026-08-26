from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ExpenseInput:
    description: str
    category: str
    amount_cents: int
    expense_date: str
    payment_method: str


class ValidationError(ValueError):
    pass


def parse_money(value: object) -> int:
    if isinstance(value, int):
        cents = value * 100
    else:
        normalized = str(value).strip()
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")

        try:
            cents = int((Decimal(normalized) * 100).quantize(Decimal("1")))
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError("amount deve ser um valor monetário válido") from exc

    if cents <= 0:
        raise ValidationError("amount deve ser maior que zero")

    return cents


def validate_expense(payload: dict[str, object]) -> ExpenseInput:
    required = ["description", "category", "amount", "expense_date", "payment_method"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]

    if missing:
        raise ValidationError(f"Campos obrigatórios ausentes: {', '.join(missing)}")

    try:
        date.fromisoformat(str(payload["expense_date"]))
    except ValueError as exc:
        raise ValidationError("expense_date deve estar no formato YYYY-MM-DD") from exc

    return ExpenseInput(
        description=str(payload["description"]).strip(),
        category=str(payload["category"]).strip().title(),
        amount_cents=parse_money(payload["amount"]),
        expense_date=str(payload["expense_date"]).strip(),
        payment_method=str(payload["payment_method"]).strip().title(),
    )


def serialize(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "description": row["description"],
        "category": row["category"],
        "amount": f"{Decimal(row['amount_cents']) / Decimal(100):.2f}",
        "expense_date": row["expense_date"],
        "payment_method": row["payment_method"],
        "created_at": row["created_at"],
    }


def create_expense(connection: sqlite3.Connection, payload: dict[str, object]) -> dict[str, object]:
    expense = validate_expense(payload)
    cursor = connection.execute(
        """
        INSERT INTO expenses (description, category, amount_cents, expense_date, payment_method)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            expense.description,
            expense.category,
            expense.amount_cents,
            expense.expense_date,
            expense.payment_method,
        ),
    )
    connection.commit()
    return get_expense(connection, cursor.lastrowid)


def get_expense(connection: sqlite3.Connection, expense_id: int) -> dict[str, object]:
    row = connection.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if row is None:
        raise KeyError("Despesa não encontrada")
    return serialize(row)


def list_expenses(
    connection: sqlite3.Connection,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, object]]:
    clauses: list[str] = []
    params: list[str] = []

    if category:
        clauses.append("category = ?")
        params.append(category.title())
    if start_date:
        clauses.append("expense_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("expense_date <= ?")
        params.append(end_date)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = connection.execute(
        f"SELECT * FROM expenses {where} ORDER BY expense_date DESC, id DESC",
        params,
    ).fetchall()
    return [serialize(row) for row in rows]


def summarize_by_category(connection: sqlite3.Connection) -> list[dict[str, object]]:
    rows = connection.execute(
        """
        SELECT category, COUNT(*) AS total_records, SUM(amount_cents) AS total_cents
        FROM expenses
        GROUP BY category
        ORDER BY total_cents DESC
        """
    ).fetchall()
    return [
        {
            "category": row["category"],
            "total_records": row["total_records"],
            "total_amount": f"{Decimal(row['total_cents']) / Decimal(100):.2f}",
        }
        for row in rows
    ]


def delete_expense(connection: sqlite3.Connection, expense_id: int) -> bool:
    cursor = connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    connection.commit()
    return cursor.rowcount > 0
