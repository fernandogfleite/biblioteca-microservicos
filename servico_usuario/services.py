"""Business logic for the user service."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from .models import ROLE_USER, VALID_ROLES, User

REQUIRED_CREATE_FIELDS = ("full_name", "email", "cpf", "password")


def init_db(db_path: str) -> None:
    """Create the database schema if it does not exist."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cpf TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT 'USER',
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        full_name=row["full_name"],
        email=row["email"],
        cpf=row["cpf"],
        role=row["role"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


def _validate_cpf_format(cpf: str) -> bool:
    """Validate that the CPF contains exactly 11 digits."""
    digits = "".join(c for c in cpf if c.isdigit())
    return len(digits) == 11


def validate_create_payload(payload: Dict[str, Any]) -> Optional[str]:
    """Validate required fields for user creation."""
    for field_name in REQUIRED_CREATE_FIELDS:
        value = payload.get(field_name)
        if value is None or str(value).strip() == "":
            return f"Campo obrigatorio ausente ou vazio: {field_name}"

    role = payload.get("role", ROLE_USER)
    if role not in VALID_ROLES:
        return f"Perfil invalido. Use: {', '.join(sorted(VALID_ROLES))}"

    cpf = str(payload.get("cpf", "")).strip()
    if not _validate_cpf_format(cpf):
        return "CPF invalido. Informe 11 digitos numericos."

    return None


def list_users(db_path: str) -> List[User]:
    """Return all users."""
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM usuarios ORDER BY full_name ASC"
        ).fetchall()
    return [_row_to_user(row) for row in rows]


def get_user(db_path: str, user_id: str) -> Optional[User]:
    """Return a user by ID, if it exists."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_email(db_path: str, email: str) -> Optional[User]:
    """Return a user by email, if it exists."""
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return _row_to_user(row) if row else None


def create_user(db_path: str, payload: Dict[str, Any]) -> User:
    """Create a new user account."""
    error = validate_create_payload(payload)
    if error:
        raise ValueError(error)

    user_id = str(uuid.uuid4())
    full_name = str(payload["full_name"]).strip()
    email = str(payload["email"]).strip().lower()
    cpf = "".join(c for c in str(payload["cpf"]) if c.isdigit())
    role = str(payload.get("role", ROLE_USER)).strip().upper()
    password_hash = generate_password_hash(str(payload["password"]))
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    with _get_connection(db_path) as conn:
        existing_email = conn.execute(
            "SELECT 1 FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if existing_email:
            raise ValueError("E-mail ja cadastrado.")

        existing_cpf = conn.execute(
            "SELECT 1 FROM usuarios WHERE cpf = ?", (cpf,)
        ).fetchone()
        if existing_cpf:
            raise ValueError("CPF ja cadastrado.")

        conn.execute(
            """
            INSERT INTO usuarios (id, full_name, email, cpf, role, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, full_name, email, cpf, role, password_hash, created_at),
        )
        conn.commit()

    return User(
        id=user_id,
        full_name=full_name,
        email=email,
        cpf=cpf,
        role=role,
        password_hash=password_hash,
        created_at=created_at,
    )


def update_user(db_path: str, user_id: str, payload: Dict[str, Any]) -> User:
    """Update an existing user's fields."""
    with _get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        if not existing:
            raise ValueError("Usuario nao encontrado.")

        updates: Dict[str, Any] = {}

        if "full_name" in payload:
            full_name = str(payload["full_name"]).strip()
            if not full_name:
                raise ValueError("Campo invalido: full_name nao pode ser vazio.")
            updates["full_name"] = full_name

        if "email" in payload:
            email = str(payload["email"]).strip().lower()
            if not email:
                raise ValueError("Campo invalido: email nao pode ser vazio.")
            conflict = conn.execute(
                "SELECT 1 FROM usuarios WHERE email = ? AND id != ?", (email, user_id)
            ).fetchone()
            if conflict:
                raise ValueError("E-mail ja cadastrado por outro usuario.")
            updates["email"] = email

        if "role" in payload:
            role = str(payload["role"]).strip().upper()
            if role not in VALID_ROLES:
                raise ValueError(f"Perfil invalido. Use: {', '.join(sorted(VALID_ROLES))}")
            updates["role"] = role

        if "password" in payload:
            password = str(payload["password"]).strip()
            if not password:
                raise ValueError("Campo invalido: password nao pode ser vazio.")
            updates["password_hash"] = generate_password_hash(password)

        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [user_id]
            conn.execute(
                f"UPDATE usuarios SET {set_clause} WHERE id = ?", values
            )
            conn.commit()

        row = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()

    return _row_to_user(row)


def delete_user(db_path: str, user_id: str) -> None:
    """Delete a user by ID."""
    with _get_connection(db_path) as conn:
        existing = conn.execute(
            "SELECT 1 FROM usuarios WHERE id = ?", (user_id,)
        ).fetchone()
        if not existing:
            raise ValueError("Usuario nao encontrado.")
        conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()


def authenticate_user(db_path: str, email: str, password: str) -> User:
    """Validate credentials and return the user if successful."""
    user = get_user_by_email(db_path, email)
    if user is None:
        raise ValueError("Credenciais invalidas.")
    if not check_password_hash(user.password_hash, password):
        raise ValueError("Credenciais invalidas.")
    return user
