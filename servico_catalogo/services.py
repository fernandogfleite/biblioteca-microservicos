"""Business logic for the catalog service."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from .models import Book

REQUIRED_FIELDS = ("titulo", "autor", "categoria")


def init_db(db_path: str) -> None:
    """Create the database schema if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS livros (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                categoria TEXT NOT NULL,
                disponivel INTEGER NOT NULL
            )
            """)
        conn.commit()


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def validate_book_payload(payload: Dict[str, Any]) -> Optional[str]:
    """Validate required book fields."""
    for field in REQUIRED_FIELDS:
        value = payload.get(field)
        if value is None or str(value).strip() == "":
            return f"Campo obrigatorio ausente ou vazio: {field}"
    return None


def _row_to_book(row: sqlite3.Row) -> Book:
    return Book(
        id=row["id"],
        titulo=row["titulo"],
        autor=row["autor"],
        categoria=row["categoria"],
        disponivel=bool(row["disponivel"]),
    )


def list_books(db_path: str) -> List[Book]:
    """Return all books from the catalog."""
    with _get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM livros ORDER BY titulo ASC").fetchall()
    return [_row_to_book(row) for row in rows]


def list_available_books(db_path: str) -> List[Book]:
    """Return only books currently available for loan."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM livros WHERE disponivel = 1 ORDER BY titulo ASC"
        ).fetchall()
    return [_row_to_book(row) for row in rows]


def get_book(db_path: str, book_id: str) -> Optional[Book]:
    """Return a book by ID, if it exists."""
    with _get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM livros WHERE id = ?", (book_id,)).fetchone()
    return _row_to_book(row) if row else None


def set_book_availability(db_path: str, book_id: str, disponivel: bool) -> Book:
    """Update the availability of a book and return the updated entity."""
    with _get_connection(db_path) as conn:
        current_row = conn.execute(
            "SELECT * FROM livros WHERE id = ?", (book_id,)
        ).fetchone()
        if not current_row:
            raise ValueError("Livro nao encontrado.")

        conn.execute(
            "UPDATE livros SET disponivel = ? WHERE id = ?",
            (int(disponivel), book_id),
        )
        conn.commit()

        updated_row = conn.execute(
            "SELECT * FROM livros WHERE id = ?", (book_id,)
        ).fetchone()

    if not updated_row:
        raise ValueError("Livro nao encontrado.")
    return _row_to_book(updated_row)


def create_book(db_path: str, payload: Dict[str, Any]) -> Book:
    """Create a new book in the catalog."""
    error = validate_book_payload(payload)
    if error:
        raise ValueError(error)

    book_id = str(payload.get("id") or uuid.uuid4())
    titulo = str(payload["titulo"]).strip()
    autor = str(payload["autor"]).strip()
    categoria = str(payload["categoria"]).strip()
    disponivel = True

    with _get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT 1 FROM livros WHERE id = ?", (book_id,)
        ).fetchone()
        if existing:
            raise ValueError("ID do livro ja existe.")

        conn.execute(
            """
            INSERT INTO livros (id, titulo, autor, categoria, disponivel)
            VALUES (?, ?, ?, ?, ?)
            """,
            (book_id, titulo, autor, categoria, int(disponivel)),
        )
        conn.commit()

    return Book(
        id=book_id,
        titulo=titulo,
        autor=autor,
        categoria=categoria,
        disponivel=disponivel,
    )
