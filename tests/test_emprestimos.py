"""Tests for the loan service."""

from __future__ import annotations

from servico_emprestimos.app import create_app
from servico_emprestimos.services import STATUS_DEVOLVIDO, STATUS_EMPRESTADO


def test_loan_creation(tmp_path):
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


def test_loan_return(tmp_path):
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
