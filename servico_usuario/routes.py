"""HTTP routes for the user service."""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, current_app, request

from .services import (
    authenticate_user,
    create_user,
    delete_user,
    get_user,
    list_users,
    update_user,
)

user_bp = Blueprint("usuarios", __name__)


def json_response(
    *,
    success: bool,
    data: Any | None = None,
    message: str | None = None,
    status: int = 200,
) -> tuple[Dict[str, Any], int]:
    """Build a standard JSON response."""
    payload: Dict[str, Any] = {"success": success}
    if success:
        payload["data"] = data
    else:
        payload["message"] = message
    return payload, status


# ── User CRUD ─────────────────────────────────────────────────────────────────


@user_bp.post("/usuarios")
def criar_usuario():
    """Create a new user account."""
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    db_path = current_app.config["DB_PATH"]

    try:
        user = create_user(db_path, payload)
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=400)

    return json_response(success=True, data=user.to_dict(), status=201)


@user_bp.get("/usuarios")
def listar_usuarios():
    """Return all users (without password hashes)."""
    db_path = current_app.config["DB_PATH"]
    users = [u.to_dict() for u in list_users(db_path)]
    return json_response(success=True, data=users)


@user_bp.get("/usuarios/<user_id>")
def buscar_usuario(user_id: str):
    """Return a single user by ID."""
    db_path = current_app.config["DB_PATH"]
    user = get_user(db_path, user_id)
    if not user:
        return json_response(
            success=False, message="Usuario nao encontrado.", status=404
        )
    return json_response(success=True, data=user.to_dict())


@user_bp.put("/usuarios/<user_id>")
def atualizar_usuario(user_id: str):
    """Update an existing user's fields."""
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    db_path = current_app.config["DB_PATH"]

    try:
        user = update_user(db_path, user_id, payload)
    except ValueError as exc:
        message = str(exc)
        status = 404 if "nao encontrado" in message else 400
        return json_response(success=False, message=message, status=status)

    return json_response(success=True, data=user.to_dict())


@user_bp.delete("/usuarios/<user_id>")
def excluir_usuario(user_id: str):
    """Delete a user by ID."""
    db_path = current_app.config["DB_PATH"]

    try:
        delete_user(db_path, user_id)
    except ValueError as exc:
        return json_response(
            success=False, message=str(exc), status=404
        )

    return json_response(success=True, data=None)


# ── Authentication ─────────────────────────────────────────────────────────────


@user_bp.post("/auth/login")
def login():
    """Authenticate a user and return a JWT token."""
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")

    if not email or not password:
        return json_response(
            success=False,
            message="Campos obrigatorios ausentes: email, password.",
            status=400,
        )

    db_path = current_app.config["DB_PATH"]

    try:
        user = authenticate_user(db_path, str(email), str(password))
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=401)

    import datetime
    import os

    import jwt

    secret = os.getenv("JWT_SECRET", "changeme-secret")
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
    token = jwt.encode(
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "exp": exp,
        },
        secret,
        algorithm="HS256",
    )

    return json_response(
        success=True,
        data={
            "token": token,
            "user": user.to_dict(),
        },
    )
