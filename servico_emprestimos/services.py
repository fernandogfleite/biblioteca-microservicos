"""Business logic for the loan service."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from .models import Loan, Reservation

STATUS_EMPRESTADO = "EMPRESTADO"
STATUS_DEVOLVIDO = "DEVOLVIDO"

STATUS_RESERVA_PENDENTE = "PENDENTE"
STATUS_RESERVA_CANCELADA = "CANCELADA"

REQUIRED_FIELDS = ("nome_usuario", "livro_id")


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def init_db(db_path: str) -> None:
    """Create the database schema if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos (
                id TEXT PRIMARY KEY,
                nome_usuario TEXT NOT NULL,
                livro_id TEXT NOT NULL,
                livro_titulo TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                user_id TEXT,
                data_emprestimo TEXT,
                data_devolucao TEXT
            )
            """)

        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(emprestimos)").fetchall()
        }
        if "livro_titulo" not in columns:
            conn.execute(
                "ALTER TABLE emprestimos ADD COLUMN livro_titulo TEXT NOT NULL DEFAULT ''"
            )
        if "user_id" not in columns:
            conn.execute("ALTER TABLE emprestimos ADD COLUMN user_id TEXT")
        if "data_emprestimo" not in columns:
            conn.execute("ALTER TABLE emprestimos ADD COLUMN data_emprestimo TEXT")
        if "data_devolucao" not in columns:
            conn.execute("ALTER TABLE emprestimos ADD COLUMN data_devolucao TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id TEXT PRIMARY KEY,
                nome_usuario TEXT NOT NULL,
                livro_id TEXT NOT NULL,
                livro_titulo TEXT NOT NULL,
                status TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT
            )
            """)

        reserva_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(reservas)").fetchall()
        }
        if "user_id" not in reserva_columns:
            conn.execute("ALTER TABLE reservas ADD COLUMN user_id TEXT")

        conn.commit()


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def validate_loan_payload(payload: Dict[str, Any]) -> Optional[str]:
    """Validate required loan fields (accepts nome_usuario or user_id)."""
    livro_id = payload.get("livro_id")
    if livro_id is None or str(livro_id).strip() == "":
        return "Campo obrigatorio ausente ou vazio: livro_id"

    has_nome = bool(payload.get("nome_usuario", "").strip() if payload.get("nome_usuario") else "")
    has_user = bool(payload.get("user_id", "").strip() if payload.get("user_id") else "")
    if not has_nome and not has_user:
        return "Campo obrigatorio ausente ou vazio: nome_usuario ou user_id"
    return None


def validate_reservation_payload(payload: Dict[str, Any]) -> Optional[str]:
    """Validate required reservation fields (accepts nome_usuario or user_id)."""
    livro_id = payload.get("livro_id")
    if livro_id is None or str(livro_id).strip() == "":
        return "Campo obrigatorio ausente ou vazio: livro_id"

    has_nome = bool(payload.get("nome_usuario", "").strip() if payload.get("nome_usuario") else "")
    has_user = bool(payload.get("user_id", "").strip() if payload.get("user_id") else "")
    if not has_nome and not has_user:
        return "Campo obrigatorio ausente ou vazio: nome_usuario ou user_id"
    return None


def _row_to_loan(row: sqlite3.Row) -> Loan:
    keys = row.keys()
    return Loan(
        id=row["id"],
        nome_usuario=row["nome_usuario"],
        livro_id=row["livro_id"],
        livro_titulo=row["livro_titulo"],
        status=row["status"],
        user_id=row["user_id"] if "user_id" in keys else None,
        data_emprestimo=row["data_emprestimo"] if "data_emprestimo" in keys else None,
        data_devolucao=row["data_devolucao"] if "data_devolucao" in keys else None,
    )


def _row_to_reservation(row: sqlite3.Row) -> Reservation:
    keys = row.keys()
    return Reservation(
        id=row["id"],
        nome_usuario=row["nome_usuario"],
        livro_id=row["livro_id"],
        livro_titulo=row["livro_titulo"],
        status=row["status"],
        criado_em=row["criado_em"],
        user_id=row["user_id"] if "user_id" in keys else None,
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


def get_loans_by_user(db_path: str, user_id: str) -> List[Loan]:
    """Return loan history for a given user_id."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM emprestimos WHERE user_id = ? ORDER BY data_emprestimo DESC, id ASC",
            (user_id,),
        ).fetchall()
    return [_row_to_loan(row) for row in rows]


def get_loans_by_book(db_path: str, livro_id: str) -> List[Loan]:
    """Return all loans (history) for a given book ID."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM emprestimos WHERE livro_id = ? ORDER BY data_emprestimo DESC, id ASC",
            (livro_id,),
        ).fetchall()
    return [_row_to_loan(row) for row in rows]


def list_reservations(db_path: str) -> List[Reservation]:
    """Return all reservations."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM reservas ORDER BY criado_em ASC, id ASC"
        ).fetchall()
    return [_row_to_reservation(row) for row in rows]


def list_pending_reservations(db_path: str) -> List[Reservation]:
    """Return only pending reservations."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM reservas
            WHERE status = ?
            ORDER BY criado_em ASC, id ASC
            """,
            (STATUS_RESERVA_PENDENTE,),
        ).fetchall()
    return [_row_to_reservation(row) for row in rows]


def get_reservation(db_path: str, reservation_id: str) -> Optional[Reservation]:
    """Return a reservation by ID, if it exists."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()
    return _row_to_reservation(row) if row else None


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


def _fetch_user_name(user_service_url: str, user_id: str) -> str:
    """Fetch a user's full_name from the user service. Returns the user_id on failure."""
    try:
        response = requests.get(f"{user_service_url}/usuarios/{user_id}", timeout=4)
    except requests.RequestException:
        return user_id

    if not response.ok:
        return user_id

    payload = response.json()
    data = payload.get("data", {})
    return str(data.get("full_name", user_id))


def create_loan(db_path: str, payload: Dict[str, Any], catalog_url: str, user_service_url: str = "") -> Loan:
    """Create a new loan with status EMPRESTADO."""
    error = validate_loan_payload(payload)
    if error:
        raise ValueError(error)

    loan_id = str(uuid.uuid4())
    user_id: Optional[str] = str(payload.get("user_id", "")).strip() or None
    livro_id = str(payload["livro_id"]).strip()
    status = STATUS_EMPRESTADO
    data_emprestimo = _now_utc()

    if user_id:
        nome_usuario = _fetch_user_name(user_service_url, user_id) if user_service_url else user_id
    else:
        nome_usuario = str(payload["nome_usuario"]).strip()

    book = _fetch_book(catalog_url, livro_id)
    livro_titulo = str(book.get("titulo", "")).strip()
    if not livro_titulo:
        raise ValueError("Resposta invalida do catalogo.")
    if not bool(book.get("disponivel", False)):
        raise ValueError("Livro indisponivel para emprestimo.")

    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO emprestimos
                (id, nome_usuario, livro_id, livro_titulo, status, user_id, data_emprestimo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (loan_id, nome_usuario, livro_id, livro_titulo, status, user_id, data_emprestimo),
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
        user_id=user_id,
        data_emprestimo=data_emprestimo,
        data_devolucao=None,
    )


def return_loan(db_path: str, loan_id: str, catalog_url: str) -> Loan:
    """Mark a loan as returned."""
    data_devolucao = _now_utc()

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
            "UPDATE emprestimos SET status = ?, data_devolucao = ? WHERE id = ?",
            (STATUS_DEVOLVIDO, data_devolucao, loan_id),
        )
        conn.commit()

    try:
        _update_book_availability(catalog_url, loan.livro_id, True)
    except ValueError:
        with _get_connection(db_path) as conn:
            conn.execute(
                "UPDATE emprestimos SET status = ?, data_devolucao = NULL WHERE id = ?",
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
        user_id=loan.user_id,
        data_emprestimo=loan.data_emprestimo,
        data_devolucao=data_devolucao,
    )


def create_reservation(
    db_path: str, payload: Dict[str, Any], catalog_url: str, user_service_url: str = ""
) -> Reservation:
    """Create a reservation for an unavailable book."""
    error = validate_reservation_payload(payload)
    if error:
        raise ValueError(error)

    reservation_id = str(uuid.uuid4())
    user_id: Optional[str] = str(payload.get("user_id", "")).strip() or None

    if user_id:
        nome_usuario = _fetch_user_name(user_service_url, user_id) if user_service_url else user_id
    else:
        nome_usuario = str(payload["nome_usuario"]).strip()

    livro_id = str(payload["livro_id"]).strip()

    book = _fetch_book(catalog_url, livro_id)
    livro_titulo = str(book.get("titulo", "")).strip()
    if not livro_titulo:
        raise ValueError("Resposta invalida do catalogo.")

    if bool(book.get("disponivel", False)):
        raise ValueError("Livro disponivel para emprestimo. Nao e necessario reservar.")

    with _get_connection(db_path) as conn:
        existing = conn.execute(
            """
            SELECT * FROM reservas
            WHERE livro_id = ?
              AND nome_usuario = ?
              AND status = ?
            """,
            (livro_id, nome_usuario, STATUS_RESERVA_PENDENTE),
        ).fetchone()

        if existing:
            raise ValueError("Usuario ja possui reserva pendente para este livro.")

        conn.execute(
            """
            INSERT INTO reservas (id, nome_usuario, livro_id, livro_titulo, status, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reservation_id,
                nome_usuario,
                livro_id,
                livro_titulo,
                STATUS_RESERVA_PENDENTE,
                user_id,
            ),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()

    return _row_to_reservation(row)


def cancel_reservation(db_path: str, reservation_id: str) -> Reservation:
    """Cancel a pending reservation."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()

        if not row:
            raise ValueError("Reserva nao encontrada.")

        reservation = _row_to_reservation(row)
        if reservation.status == STATUS_RESERVA_CANCELADA:
            raise ValueError("Reserva ja cancelada.")

        conn.execute(
            "UPDATE reservas SET status = ? WHERE id = ?",
            (STATUS_RESERVA_CANCELADA, reservation_id),
        )
        conn.commit()

        updated = conn.execute(
            "SELECT * FROM reservas WHERE id = ?", (reservation_id,)
        ).fetchone()

    return _row_to_reservation(updated)


