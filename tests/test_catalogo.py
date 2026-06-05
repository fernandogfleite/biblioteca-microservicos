"""Tests for the catalog service."""

from __future__ import annotations

from servico_catalogo.app import create_app


def test_book_creation(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()

    response = client.post(
        "/livros",
        json={"titulo": "Dom Casmurro", "autor": "Machado de Assis", "categoria": "Classico"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["disponivel"] is True
    assert payload["data"]["titulo"] == "Dom Casmurro"


def test_book_listing(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()

    client.post(
        "/livros",
        json={"titulo": "Book A", "autor": "Autor A", "categoria": "Ficcao"},
    )
    client.post(
        "/livros",
        json={"titulo": "Book B", "autor": "Autor B", "categoria": "Drama"},
    )

    response = client.get("/livros")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert len(payload["data"]) == 2
