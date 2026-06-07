"""Tests for the loan service."""

from __future__ import annotations

from servico_emprestimos import services
from servico_emprestimos.app import create_app
from servico_emprestimos.services import STATUS_DEVOLVIDO, STATUS_EMPRESTADO


def test_loan_creation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Teste",
            "disponivel": True,
        },
    )
    monkeypatch.setattr(
        services, "_update_book_availability", lambda *args, **kwargs: None
    )

    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    response = client.post(
        "/emprestimos",
        json={"nome_usuario": "Ana", "livro_id": "book-1"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["status"] == STATUS_EMPRESTADO
    assert payload["data"]["livro_titulo"] == "Livro Teste"


def test_loan_return(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Devolucao",
            "disponivel": True,
        },
    )
    monkeypatch.setattr(
        services, "_update_book_availability", lambda *args, **kwargs: None
    )

    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    create_response = client.post(
        "/emprestimos",
        json={"nome_usuario": "Joao", "livro_id": "book-2"},
    )
    loan_id = create_response.get_json()["data"]["id"]

    response = client.post("/devolucoes", json={"emprestimo_id": loan_id})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["status"] == STATUS_DEVOLVIDO
    assert payload["data"]["livro_titulo"] == "Livro Devolucao"


def test_open_loans_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Aberto",
            "disponivel": True,
        },
    )
    monkeypatch.setattr(
        services, "_update_book_availability", lambda *args, **kwargs: None
    )

    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    create_response = client.post(
        "/emprestimos",
        json={"nome_usuario": "Maria", "livro_id": "book-3"},
    )
    loan_id = create_response.get_json()["data"]["id"]

    open_response = client.get("/emprestimos/abertos")
    open_payload = open_response.get_json()
    assert open_response.status_code == 200
    assert len(open_payload["data"]) == 1
    assert open_payload["data"][0]["id"] == loan_id
    assert open_payload["data"][0]["livro_titulo"] == "Livro Aberto"

    client.post("/devolucoes", json={"emprestimo_id": loan_id})
    open_response_after_return = client.get("/emprestimos/abertos")
    open_payload_after_return = open_response_after_return.get_json()
    assert open_response_after_return.status_code == 200
    assert open_payload_after_return["data"] == []


def test_loan_creation_fails_when_book_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Indisponivel",
            "disponivel": False,
        },
    )

    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    response = client.post(
        "/emprestimos",
        json={"nome_usuario": "Ana", "livro_id": "book-1"},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["success"] is False
    assert payload["message"] == "Livro indisponivel para emprestimo."
