from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from database import connect, migrate
from expenses import (
    ValidationError,
    create_expense,
    delete_expense,
    get_expense,
    list_expenses,
    summarize_by_category,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "data" / "expenses.db"


class ExpenseApiHandler(BaseHTTPRequestHandler):
    database_path = DEFAULT_DATABASE

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self.respond({"status": "ok"})
            return

        if parsed.path == "/expenses":
            query = parse_qs(parsed.query)
            with self.open_connection() as connection:
                records = list_expenses(
                    connection,
                    category=first(query, "category"),
                    start_date=first(query, "start_date"),
                    end_date=first(query, "end_date"),
                )
            self.respond({"data": records})
            return

        if parsed.path == "/reports/categories":
            with self.open_connection() as connection:
                records = summarize_by_category(connection)
            self.respond({"data": records})
            return

        if parsed.path.startswith("/expenses/"):
            try:
                expense_id = int(parsed.path.rsplit("/", 1)[1])
                with self.open_connection() as connection:
                    expense = get_expense(connection, expense_id)
                self.respond({"data": expense})
            except (ValueError, KeyError):
                self.respond_error(HTTPStatus.NOT_FOUND, "Despesa não encontrada")
            return

        self.respond_error(HTTPStatus.NOT_FOUND, "Rota não encontrada")

    def do_POST(self) -> None:
        if self.path != "/expenses":
            self.respond_error(HTTPStatus.NOT_FOUND, "Rota não encontrada")
            return

        try:
            payload = self.read_json()
            with self.open_connection() as connection:
                expense = create_expense(connection, payload)
            self.respond({"data": expense}, HTTPStatus.CREATED)
        except ValidationError as exc:
            self.respond_error(HTTPStatus.BAD_REQUEST, str(exc))
        except json.JSONDecodeError:
            self.respond_error(HTTPStatus.BAD_REQUEST, "JSON inválido")

    def do_DELETE(self) -> None:
        if not self.path.startswith("/expenses/"):
            self.respond_error(HTTPStatus.NOT_FOUND, "Rota não encontrada")
            return

        try:
            expense_id = int(self.path.rsplit("/", 1)[1])
        except ValueError:
            self.respond_error(HTTPStatus.NOT_FOUND, "Despesa não encontrada")
            return

        with self.open_connection() as connection:
            deleted = delete_expense(connection, expense_id)

        if deleted:
            self.respond({"deleted": True})
        else:
            self.respond_error(HTTPStatus.NOT_FOUND, "Despesa não encontrada")

    def read_json(self) -> dict[str, object]:
        size = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(size).decode("utf-8")
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise ValidationError("O corpo da requisição deve ser um objeto JSON")
        return payload

    def respond(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def respond_error(self, status: HTTPStatus, message: str) -> None:
        self.respond({"error": message}, status)

    def open_connection(self):
        connection = connect(self.database_path)
        migrate(connection)
        return connection

    def log_message(self, format: str, *args: object) -> None:
        return


def first(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="API REST para gestão de despesas.")
    parser.add_argument("--host", default="127.0.0.1", help="Host da API.")
    parser.add_argument("--port", type=int, default=8000, help="Porta da API.")
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Caminho do banco SQLite.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    ExpenseApiHandler.database_path = args.database

    with connect(args.database) as connection:
        migrate(connection)

    server = ThreadingHTTPServer((args.host, args.port), ExpenseApiHandler)
    print(f"API disponível em http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
