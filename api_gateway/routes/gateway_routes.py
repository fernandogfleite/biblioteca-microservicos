"""Gateway routes that forward requests to microservices."""

from __future__ import annotations

import os
from collections import Counter
from functools import wraps
from typing import Any, Callable, Dict, Optional

import jwt
import requests
from flask import Blueprint, request

gateway_bp = Blueprint("gateway", __name__)

CATALOGO_URL = os.getenv(
    "CATALOG_SERVICE_URL",
    os.getenv("CATALOGO_SERVICE_URL", "http://localhost:5001"),
)
EMPRESTIMOS_URL = os.getenv(
    "LOANS_SERVICE_URL",
    os.getenv("EMPRESTIMOS_SERVICE_URL", "http://localhost:5002"),
)
RECOMENDACOES_URL = os.getenv(
    "RECOMMENDATION_SERVICE_URL",
    os.getenv("RECOMENDACOES_SERVICE_URL", "http://localhost:5003"),
)
USUARIOS_URL = os.getenv(
    "USER_SERVICE_URL",
    os.getenv("USUARIOS_SERVICE_URL", "http://localhost:5004"),
)

_JWT_SECRET = os.getenv("JWT_SECRET", "changeme-secret")


# ── Helpers ───────────────────────────────────────────────────────────────────


def json_response(
    *,
    success: bool,
    data: Any | None = None,
    message: str | None = None,
    status: int = 200,
) -> tuple[Dict[str, Any], int]:
    payload: Dict[str, Any] = {"success": success}
    if success:
        payload["data"] = data
    else:
        payload["message"] = message
    return payload, status


def _forward(
    method: str,
    url: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, Any], int]:
    try:
        response = requests.request(
            method, url, json=json_body, params=params, timeout=4
        )
    except requests.RequestException:
        return json_response(
            success=False,
            message="Falha ao comunicar com o servico solicitado.",
            status=502,
        )

    try:
        payload = response.json()
    except ValueError:
        return json_response(
            success=False,
            message="Resposta invalida do servico solicitado.",
            status=502,
        )

    return payload, response.status_code


def _decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token. Returns None on failure."""
    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _get_token_claims() -> Optional[Dict[str, Any]]:
    """Extract and decode the Bearer token from the request headers."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    return _decode_token(token)


# ── Auth decorators ───────────────────────────────────────────────────────────


def require_auth(f: Callable) -> Callable:
    """Decorator: require a valid JWT token."""

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        claims = _get_token_claims()
        if claims is None:
            return json_response(
                success=False,
                message="Autenticacao necessaria. Faca login para continuar.",
                status=401,
            )
        return f(*args, **kwargs)

    return wrapper


def require_admin(f: Callable) -> Callable:
    """Decorator: require a valid JWT token with ADMIN role."""

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        claims = _get_token_claims()
        if claims is None:
            return json_response(
                success=False,
                message="Autenticacao necessaria. Faca login para continuar.",
                status=401,
            )
        if claims.get("role") != "ADMIN":
            return json_response(
                success=False,
                message="Acesso negado. Permissao de administrador necessaria.",
                status=403,
            )
        return f(*args, **kwargs)

    return wrapper


# ── Catalog routes ────────────────────────────────────────────────────────────


@gateway_bp.get("/livros")
def listar_livros():
    """List books with optional filters (titulo, autor, categoria, disponivel)."""
    params: Dict[str, Any] = {}
    for key in ("titulo", "autor", "categoria", "disponivel"):
        value = request.args.get(key)
        if value is not None:
            params[key] = value
    return _forward("GET", f"{CATALOGO_URL}/livros", params=params if params else None)


@gateway_bp.get("/livros/disponiveis")
def listar_livros_disponiveis():
    return _forward("GET", f"{CATALOGO_URL}/livros/disponiveis")


@gateway_bp.get("/livros/<book_id>")
def buscar_livro(book_id: str):
    return _forward("GET", f"{CATALOGO_URL}/livros/{book_id}")


@gateway_bp.post("/livros")
@require_admin
def criar_livro():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{CATALOGO_URL}/livros", json_body=payload)


@gateway_bp.patch("/livros/<book_id>/disponibilidade")
@require_admin
def atualizar_disponibilidade_livro(book_id: str):
    payload = request.get_json(silent=True) or {}
    return _forward(
        "PATCH",
        f"{CATALOGO_URL}/livros/{book_id}/disponibilidade",
        json_body=payload,
    )


@gateway_bp.get("/livros/<book_id>/historico-emprestimos")
@require_auth
def historico_emprestimos_livro(book_id: str):
    """Return the loan history for a specific book."""
    return _forward("GET", f"{EMPRESTIMOS_URL}/emprestimos/livro/{book_id}")


# ── Loan routes ───────────────────────────────────────────────────────────────


@gateway_bp.get("/emprestimos")
@require_admin
def listar_emprestimos():
    return _forward("GET", f"{EMPRESTIMOS_URL}/emprestimos")


@gateway_bp.get("/emprestimos/abertos")
@require_admin
def listar_emprestimos_abertos():
    return _forward("GET", f"{EMPRESTIMOS_URL}/emprestimos/abertos")


@gateway_bp.post("/emprestimos")
@require_auth
def criar_emprestimo():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{EMPRESTIMOS_URL}/emprestimos", json_body=payload)


@gateway_bp.post("/devolucoes")
@require_auth
def devolver_emprestimo():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{EMPRESTIMOS_URL}/devolucoes", json_body=payload)


@gateway_bp.get("/reservas")
@require_auth
def listar_reservas():
    return _forward("GET", f"{EMPRESTIMOS_URL}/reservas")


@gateway_bp.get("/reservas/pendentes")
@require_auth
def listar_reservas_pendentes():
    return _forward("GET", f"{EMPRESTIMOS_URL}/reservas/pendentes")


@gateway_bp.post("/reservas")
@require_auth
def criar_reserva():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{EMPRESTIMOS_URL}/reservas", json_body=payload)


@gateway_bp.post("/reservas/cancelar")
@require_auth
def cancelar_reserva():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{EMPRESTIMOS_URL}/reservas/cancelar", json_body=payload)


# ── Recommendation routes ─────────────────────────────────────────────────────


@gateway_bp.get("/recomendacoes/<categoria>")
def recomendar_livros(categoria: str):
    return _forward("GET", f"{RECOMENDACOES_URL}/recomendacoes/{categoria}")


# ── User / Auth routes ────────────────────────────────────────────────────────


@gateway_bp.post("/auth/login")
def login():
    """Authenticate a user and return a JWT token."""
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{USUARIOS_URL}/auth/login", json_body=payload)


@gateway_bp.post("/usuarios")
def criar_usuario():
    """Create a new user account (public endpoint for self-registration)."""
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{USUARIOS_URL}/usuarios", json_body=payload)


@gateway_bp.get("/usuarios")
@require_admin
def listar_usuarios():
    return _forward("GET", f"{USUARIOS_URL}/usuarios")


@gateway_bp.get("/usuarios/<user_id>")
@require_auth
def buscar_usuario(user_id: str):
    return _forward("GET", f"{USUARIOS_URL}/usuarios/{user_id}")


@gateway_bp.put("/usuarios/<user_id>")
@require_auth
def atualizar_usuario(user_id: str):
    payload = request.get_json(silent=True) or {}
    return _forward("PUT", f"{USUARIOS_URL}/usuarios/{user_id}", json_body=payload)


@gateway_bp.delete("/usuarios/<user_id>")
@require_admin
def excluir_usuario(user_id: str):
    return _forward("DELETE", f"{USUARIOS_URL}/usuarios/{user_id}")


@gateway_bp.get("/usuarios/<user_id>/historico-emprestimos")
@require_auth
def historico_emprestimos_usuario(user_id: str):
    """Return the loan history for a specific user."""
    return _forward("GET", f"{EMPRESTIMOS_URL}/emprestimos/usuario/{user_id}")


# ── Dashboard ─────────────────────────────────────────────────────────────────


@gateway_bp.get("/dashboard")
@require_admin
def dashboard():
    """Aggregate metrics from all services for the admin dashboard."""
    livros_result, livros_status = _forward("GET", f"{CATALOGO_URL}/livros")
    usuarios_result, usuarios_status = _forward("GET", f"{USUARIOS_URL}/usuarios")
    emprestimos_result, emprestimos_status = _forward(
        "GET", f"{EMPRESTIMOS_URL}/emprestimos"
    )

    livros: list = (
        livros_result.get("data", [])
        if livros_status == 200 and livros_result.get("success")
        else []
    )
    usuarios: list = (
        usuarios_result.get("data", [])
        if usuarios_status == 200 and usuarios_result.get("success")
        else []
    )
    emprestimos: list = (
        emprestimos_result.get("data", [])
        if emprestimos_status == 200 and emprestimos_result.get("success")
        else []
    )

    total_livros = len(livros)
    disponiveis = sum(1 for b in livros if b.get("disponivel"))
    indisponiveis = total_livros - disponiveis

    total_usuarios = len(usuarios)

    total_emprestimos = len(emprestimos)
    emprestimos_abertos = sum(
        1 for e in emprestimos if e.get("status") == "EMPRESTADO"
    )
    emprestimos_devolvidos = sum(
        1 for e in emprestimos if e.get("status") == "DEVOLVIDO"
    )

    livro_counter: Counter = Counter(
        e["livro_id"] for e in emprestimos if e.get("livro_id")
    )
    livro_titulo_map = {
        e["livro_id"]: e.get("livro_titulo", e["livro_id"])
        for e in emprestimos
        if e.get("livro_id")
    }
    livros_mais_emprestados = [
        {"livro_id": lid, "titulo": livro_titulo_map.get(lid, lid), "total": count}
        for lid, count in livro_counter.most_common(10)
    ]

    user_counter: Counter = Counter(
        e.get("user_id") or e.get("nome_usuario", "")
        for e in emprestimos
        if e.get("user_id") or e.get("nome_usuario")
    )
    usuarios_mais_ativos = [
        {"identificador": uid, "total": count}
        for uid, count in user_counter.most_common(10)
        if uid
    ]

    return json_response(
        success=True,
        data={
            "livros": {
                "total": total_livros,
                "disponiveis": disponiveis,
                "indisponiveis": indisponiveis,
            },
            "usuarios": {"total": total_usuarios},
            "emprestimos": {
                "total": total_emprestimos,
                "abertos": emprestimos_abertos,
                "devolvidos": emprestimos_devolvidos,
            },
            "livros_mais_emprestados": livros_mais_emprestados,
            "usuarios_mais_ativos": usuarios_mais_ativos,
        },
    )

