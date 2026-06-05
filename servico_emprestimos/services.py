"""Business logic for the loan service."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from .models import Loan

STATUS_EMPRESTADO = "EMPRESTADO"
STATUS_DEVOLVIDO = "DEVOLVIDO"
REQUIRED_FIELDS = ("nome_usuario", "livro_id")


def init_db(db_path: str) -> None:
    """Create the database schema if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emprestimos (
                id TEXT PRIMARY KEY,
                nome_usuario TEXT NOT NULL,
                livro_id TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
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
        status=row["status"],
    )


def list_loans(db_path: str) -> List[Loan]:
    """Return all loans."""
    with _get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM emprestimos ORDER BY id ASC").fetchall()
    return [_row_to_loan(row) for row in rows]


def get_loan(db_path: str, loan_id: str) -> Optional[Loan]:
    """Return a loan by ID, if it exists."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM emprestimos WHERE id = ?", (loan_id,)
        ).fetchone()
    return _row_to_loan(row) if row else None


def create_loan(db_path: str, payload: Dict[str, Any]) -> Loan:
    """Create a new loan with status EMPRESTADO."""
    error = validate_loan_payload(payload)
    if error:
        raise ValueError(error)

    loan_id = str(uuid.uuid4())
    nome_usuario = str(payload["nome_usuario"]).strip()
    livro_id = str(payload["livro_id"]).strip()
    status = STATUS_EMPRESTADO

    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO emprestimos (id, nome_usuario, livro_id, status)
            VALUES (?, ?, ?, ?)
            """,
            (loan_id, nome_usuario, livro_id, status),
        )
        conn.commit()

    return Loan(
        id=loan_id,
        nome_usuario=nome_usuario,
        livro_id=livro_id,
        status=status,
    )


def return_loan(db_path: str, loan_id: str) -> Loan:
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

    return Loan(
        id=loan.id,
        nome_usuario=loan.nome_usuario,
        livro_id=loan.livro_id,
        status=STATUS_DEVOLVIDO,
    )
