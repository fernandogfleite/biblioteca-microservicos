"""Tests for the recommendation service."""

from __future__ import annotations

from servico_recomendacao import services
from servico_recomendacao.app import create_app


def test_recommendation_query(monkeypatch):
    catalog_books = [
        {"id": "1", "titulo": "Livro A", "autor": "Autor A", "categoria": "Ficcao"},
        {"id": "2", "titulo": "Livro B", "autor": "Autor B", "categoria": "Drama"},
    ]

    monkeypatch.setattr(services, "fetch_catalog_books", lambda base_url: catalog_books)

    app = create_app({"TESTING": True})
    client = app.test_client()

    response = client.get("/recomendacoes/Ficcao")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["categoria"] == "Ficcao"
