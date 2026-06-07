"""Business logic for the loan service."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Dict, List, Optional

import requests

from .models import Loan

STATUS_EMPRESTADO = "EMPRESTADO"
STATUS_DEVOLVIDO = "DEVOLVIDO"
REQUIRED_FIELDS = ("nome_usuario", "livro_id")


def init_db(db_path: str) -> None:
    """Create the database schema if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos (
                id TEXT PRIMARY KEY,
                nome_usuario TEXT NOT NULL,
                livro_id TEXT NOT NULL,
                livro_titulo TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL
            )
            """)

        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(emprestimos)").fetchall()
        }
        if "livro_titulo" not in columns:
            conn.execute(
                "ALTER TABLE emprestimos ADD COLUMN livro_titulo TEXT NOT NULL DEFAULT ''"
            )

        conn.commit()


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def validate_loan_payload(payload: Dict[str, Any]) -> Optional[str]:
    """Validate required loan fields."""
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or str(value).strip() == "":
            return f"Campo obrigatorio ausente ou vazio: {field}"
    return None


def _row_to_loan(row: sqlite3.Row) -> Loan:
    return Loan(
        id=row["id"],
        nome_usuario=row["nome_usuario"],
        livro_id=row["livro_id"],
        livro_titulo=row["livro_titulo"],
        status=row["status"],
    )


def list_loans(db_path: str) -> List[Loan]:
    """Return all loans."""
    with _get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM emprestimos ORDER BY id ASC").fetchall()
    return [_row_to_loan(row) for row in rows]


def list_open_loans(db_path: str) -> List[Loan]:
    """Return only loans that are currently open."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM emprestimos WHERE status = ? ORDER BY id ASC",
            (STATUS_EMPRESTADO,),
        ).fetchall()
    return [_row_to_loan(row) for row in rows]


def get_loan(db_path: str, loan_id: str) -> Optional[Loan]:
    """Return a loan by ID, if it exists."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM emprestimos WHERE id = ?", (loan_id,)
        ).fetchone()
    return _row_to_loan(row) if row else None


def _fetch_book(catalog_url: str, book_id: str) -> Dict[str, Any]:
    """Fetch book data from catalog service."""
    try:
        response = requests.get(f"{catalog_url}/livros/{book_id}", timeout=4)
    except requests.RequestException as exc:
        raise ValueError("Falha ao consultar o catalogo.") from exc

    if response.status_code == 404:
        raise ValueError("Livro nao encontrado no catalogo.")
    if not response.ok:
        raise ValueError("Falha ao consultar o catalogo.")

    payload = response.json()
    if not payload.get("success"):
        raise ValueError(payload.get("message") or "Falha ao consultar o catalogo.")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Resposta invalida do catalogo.")
    return data


def _update_book_availability(catalog_url: str, book_id: str, disponivel: bool) -> None:
    """Update book availability in catalog service."""
    try:
        response = requests.patch(
            f"{catalog_url}/livros/{book_id}/disponibilidade",
            json={"disponivel": disponivel},
            timeout=4,
        )
    except requests.RequestException as exc:
        raise ValueError("Falha ao atualizar disponibilidade no catalogo.") from exc

    if not response.ok:
        raise ValueError("Falha ao atualizar disponibilidade no catalogo.")

    payload = response.json()
    if not payload.get("success"):
        raise ValueError(
            payload.get("message") or "Falha ao atualizar disponibilidade no catalogo."
        )


def create_loan(db_path: str, payload: Dict[str, Any], catalog_url: str) -> Loan:
    """Create a new loan with status EMPRESTADO."""
    error = validate_loan_payload(payload)
    if error:
        raise ValueError(error)

    loan_id = str(uuid.uuid4())
    nome_usuario = str(payload["nome_usuario"]).strip()
    livro_id = str(payload["livro_id"]).strip()
    status = STATUS_EMPRESTADO

    book = _fetch_book(catalog_url, livro_id)
    livro_titulo = str(book.get("titulo", "")).strip()
    if not livro_titulo:
        raise ValueError("Resposta invalida do catalogo.")
    if not bool(book.get("disponivel", False)):
        raise ValueError("Livro indisponivel para emprestimo.")

    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO emprestimos (id, nome_usuario, livro_id, livro_titulo, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (loan_id, nome_usuario, livro_id, livro_titulo, status),
        )
        conn.commit()

    try:
        _update_book_availability(catalog_url, livro_id, False)
    except ValueError:
        with _get_connection(db_path) as conn:
            conn.execute("DELETE FROM emprestimos WHERE id = ?", (loan_id,))
            conn.commit()
        raise

    return Loan(
        id=loan_id,
        nome_usuario=nome_usuario,
        livro_id=livro_id,
        livro_titulo=livro_titulo,
        status=status,
    )


def return_loan(db_path: str, loan_id: str, catalog_url: str) -> Loan:
    """Mark a loan as returned."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM emprestimos WHERE id = ?", (loan_id,)
        ).fetchone()
        if not row:
            raise ValueError("Emprestimo nao encontrado.")

        loan = _row_to_loan(row)
        if loan.status == STATUS_DEVOLVIDO:
            raise ValueError("Emprestimo ja devolvido.")

        conn.execute(
            "UPDATE emprestimos SET status = ? WHERE id = ?",
            (STATUS_DEVOLVIDO, loan_id),
        )
        conn.commit()

    try:
        _update_book_availability(catalog_url, loan.livro_id, True)
    except ValueError:
        with _get_connection(db_path) as conn:
            conn.execute(
                "UPDATE emprestimos SET status = ? WHERE id = ?",
                (STATUS_EMPRESTADO, loan_id),
            )
            conn.commit()
        raise

    return Loan(
        id=loan.id,
        nome_usuario=loan.nome_usuario,
        livro_id=loan.livro_id,
        livro_titulo=loan.livro_titulo,
        status=STATUS_DEVOLVIDO,
    )
