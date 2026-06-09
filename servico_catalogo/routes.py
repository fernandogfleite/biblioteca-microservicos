"""HTTP routes for the catalog service."""

from __future__ import annotations

from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from .services import (
    create_book,
    get_book,
    list_available_books,
    list_books,
    search_books,
    set_book_availability,
)

catalog_bp = Blueprint("catalogo", __name__)


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


@catalog_bp.get("/livros")
def listar_livros():
    """List books; supports optional query filters: titulo, autor, categoria, disponivel."""
    db_path = current_app.config["DB_PATH"]

    titulo = request.args.get("titulo", "").strip() or None
    autor = request.args.get("autor", "").strip() or None
    categoria = request.args.get("categoria", "").strip() or None
    disponivel_raw = request.args.get("disponivel")
    disponivel: bool | None = None
    if disponivel_raw is not None:
        disponivel = disponivel_raw.lower() in {"true", "1", "yes"}

    if titulo or autor or categoria or disponivel is not None:
        books = [book.to_dict() for book in search_books(db_path, titulo, autor, categoria, disponivel)]
    else:
        books = [book.to_dict() for book in list_books(db_path)]

    return json_response(success=True, data=books)


@catalog_bp.get("/livros/disponiveis")
def listar_livros_disponiveis():
    db_path = current_app.config["DB_PATH"]
    books = [book.to_dict() for book in list_available_books(db_path)]
    return json_response(success=True, data=books)


@catalog_bp.get("/livros/<book_id>")
def buscar_livro(book_id: str):
    db_path = current_app.config["DB_PATH"]
    book = get_book(db_path, book_id)
    if not book:
        return json_response(success=False, message="Livro nao encontrado.", status=404)
    return json_response(success=True, data=book.to_dict())


@catalog_bp.post("/livros")
def criar_livro():
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    db_path = current_app.config["DB_PATH"]
    try:
        book = create_book(db_path, payload)
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=400)

    return json_response(success=True, data=book.to_dict(), status=201)


@catalog_bp.patch("/livros/<book_id>/disponibilidade")
def atualizar_disponibilidade_livro(book_id: str):
    if not request.is_json:
        return json_response(
            success=False, message="Corpo da requisicao deve ser JSON.", status=400
        )

    payload = request.get_json(silent=True) or {}
    if "disponivel" not in payload or not isinstance(payload["disponivel"], bool):
        return json_response(
            success=False,
            message="Campo obrigatorio invalido: disponivel (bool).",
            status=400,
        )

    db_path = current_app.config["DB_PATH"]
    try:
        book = set_book_availability(db_path, book_id, payload["disponivel"])
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=404)

    return json_response(success=True, data=book.to_dict())
