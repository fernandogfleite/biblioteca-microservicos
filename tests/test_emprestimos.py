"""Tests for the loan service."""

from __future__ import annotations

from servico_emprestimos import services
from servico_emprestimos.app import create_app
from servico_emprestimos.services import (
    STATUS_DEVOLVIDO,
    STATUS_EMPRESTADO,
    STATUS_RESERVA_CANCELADA,
    STATUS_RESERVA_PENDENTE,
)


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

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
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

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
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

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
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

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    response = client.post(
        "/emprestimos",
        json={"nome_usuario": "Ana", "livro_id": "book-1"},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["success"] is False
    assert payload["message"] == "Livro indisponivel para emprestimo."


def test_reservation_creation_for_unavailable_book(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Reservado",
            "disponivel": False,
        },
    )

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    response = client.post(
        "/reservas",
        json={"nome_usuario": "Carlos", "livro_id": "book-10"},
    )
    payload = response.get_json()

    assert response.status_code == 201
    assert payload["success"] is True
    assert payload["data"]["nome_usuario"] == "Carlos"
    assert payload["data"]["livro_id"] == "book-10"
    assert payload["data"]["livro_titulo"] == "Livro Reservado"
    assert payload["data"]["status"] == STATUS_RESERVA_PENDENTE
    assert "criado_em" in payload["data"]

    list_response = client.get("/reservas")
    list_payload = list_response.get_json()

    assert list_response.status_code == 200
    assert list_payload["success"] is True
    assert len(list_payload["data"]) == 1
    assert list_payload["data"][0]["livro_titulo"] == "Livro Reservado"


def test_reservation_creation_fails_when_book_available(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Disponivel",
            "disponivel": True,
        },
    )

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    response = client.post(
        "/reservas",
        json={"nome_usuario": "Carlos", "livro_id": "book-11"},
    )
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["success"] is False
    assert (
        payload["message"]
        == "Livro disponivel para emprestimo. Nao e necessario reservar."
    )


def test_pending_reservations_listing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Pendente",
            "disponivel": False,
        },
    )

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    create_response = client.post(
        "/reservas",
        json={"nome_usuario": "Beatriz", "livro_id": "book-12"},
    )
    reservation_id = create_response.get_json()["data"]["id"]

    pending_response = client.get("/reservas/pendentes")
    pending_payload = pending_response.get_json()

    assert pending_response.status_code == 200
    assert pending_payload["success"] is True
    assert len(pending_payload["data"]) == 1
    assert pending_payload["data"][0]["id"] == reservation_id
    assert pending_payload["data"][0]["status"] == STATUS_RESERVA_PENDENTE


def test_reservation_cancel(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Cancelamento",
            "disponivel": False,
        },
    )

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    create_response = client.post(
        "/reservas",
        json={"nome_usuario": "Daniel", "livro_id": "book-13"},
    )
    reservation_id = create_response.get_json()["data"]["id"]

    cancel_response = client.post(
        "/reservas/cancelar",
        json={"reserva_id": reservation_id},
    )
    cancel_payload = cancel_response.get_json()

    assert cancel_response.status_code == 200
    assert cancel_payload["success"] is True
    assert cancel_payload["data"]["id"] == reservation_id
    assert cancel_payload["data"]["status"] == STATUS_RESERVA_CANCELADA

    pending_response = client.get("/reservas/pendentes")
    pending_payload = pending_response.get_json()

    assert pending_response.status_code == 200
    assert pending_payload["success"] is True
    assert pending_payload["data"] == []


def test_duplicate_pending_reservation_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(
        services,
        "_fetch_book",
        lambda catalog_url, book_id: {
            "id": book_id,
            "titulo": "Livro Duplicado",
            "disponivel": False,
        },
    )

    app = create_app(
        {"TESTING": True, "DB_PATH": str(tmp_path / "emprestimos.db")})
    client = app.test_client()

    first_response = client.post(
        "/reservas",
        json={"nome_usuario": "Eduarda", "livro_id": "book-14"},
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/reservas",
        json={"nome_usuario": "Eduarda", "livro_id": "book-14"},
    )
    second_payload = second_response.get_json()

    assert second_response.status_code == 400
    assert second_payload["success"] is False
    assert second_payload["message"] == "Usuario ja possui reserva pendente para este livro."
