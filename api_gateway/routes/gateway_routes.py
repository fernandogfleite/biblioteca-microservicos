"""Gateway routes that forward requests to microservices."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

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
    method: str, url: str, *, json_body: Optional[Dict[str, Any]] = None
) -> tuple[Dict[str, Any], int]:
    try:
        response = requests.request(method, url, json=json_body, timeout=4)
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


@gateway_bp.get("/livros")
def listar_livros():
    return _forward("GET", f"{CATALOGO_URL}/livros")


@gateway_bp.get("/livros/disponiveis")
def listar_livros_disponiveis():
    return _forward("GET", f"{CATALOGO_URL}/livros/disponiveis")


@gateway_bp.get("/livros/<book_id>")
def buscar_livro(book_id: str):
    return _forward("GET", f"{CATALOGO_URL}/livros/{book_id}")


@gateway_bp.post("/livros")
def criar_livro():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{CATALOGO_URL}/livros", json_body=payload)


@gateway_bp.patch("/livros/<book_id>/disponibilidade")
def atualizar_disponibilidade_livro(book_id: str):
    payload = request.get_json(silent=True) or {}
    return _forward(
        "PATCH",
        f"{CATALOGO_URL}/livros/{book_id}/disponibilidade",
        json_body=payload,
    )


@gateway_bp.get("/emprestimos")
def listar_emprestimos():
    return _forward("GET", f"{EMPRESTIMOS_URL}/emprestimos")


@gateway_bp.get("/emprestimos/abertos")
def listar_emprestimos_abertos():
    return _forward("GET", f"{EMPRESTIMOS_URL}/emprestimos/abertos")


@gateway_bp.post("/emprestimos")
def criar_emprestimo():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{EMPRESTIMOS_URL}/emprestimos", json_body=payload)


@gateway_bp.post("/devolucoes")
def devolver_emprestimo():
    payload = request.get_json(silent=True) or {}
    return _forward("POST", f"{EMPRESTIMOS_URL}/devolucoes", json_body=payload)


@gateway_bp.get("/recomendacoes/<categoria>")
def recomendar_livros(categoria: str):
    return _forward("GET", f"{RECOMENDACOES_URL}/recomendacoes/{categoria}")
