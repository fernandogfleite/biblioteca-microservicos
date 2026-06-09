"""Tests for the catalog service."""

from __future__ import annotations

from servico_catalogo.app import create_app


def test_book_creation(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()

    response = client.post(
        "/livros",
        json={
            "titulo": "Dom Casmurro",
            "autor": "Machado de Assis",
            "categoria": "Classico",
        },
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


def test_available_books_listing(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()

    created_response = client.post(
        "/livros",
        json={"titulo": "Book A", "autor": "Autor A", "categoria": "Ficcao"},
    )
    created_book = created_response.get_json()["data"]

    client.post(
        "/livros",
        json={"titulo": "Book B", "autor": "Autor B", "categoria": "Drama"},
    )

    client.patch(
        f"/livros/{created_book['id']}/disponibilidade",
        json={"disponivel": False},
    )

    response = client.get("/livros/disponiveis")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["titulo"] == "Book B"


def test_update_book_availability(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()

    created_response = client.post(
        "/livros",
        json={"titulo": "Book C", "autor": "Autor C", "categoria": "Drama"},
    )
    book = created_response.get_json()["data"]

    update_response = client.patch(
        f"/livros/{book['id']}/disponibilidade",
        json={"disponivel": False},
    )
    update_payload = update_response.get_json()

    assert update_response.status_code == 200
    assert update_payload["success"] is True
    assert update_payload["data"]["disponivel"] is False


# ── Filter / search tests ─────────────────────────────────────────────────────


def _seed_books(client):
    """Create a set of known books for filter testing."""
    client.post(
        "/livros",
        json={"titulo": "Dom Casmurro", "autor": "Machado de Assis", "categoria": "Classico"},
    )
    client.post(
        "/livros",
        json={"titulo": "A Hora da Estrela", "autor": "Clarice Lispector", "categoria": "Romance"},
    )
    client.post(
        "/livros",
        json={"titulo": "O Cortico", "autor": "Aluisio Azevedo", "categoria": "Classico"},
    )


def test_filter_by_titulo(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    response = client.get("/livros?titulo=dom")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["titulo"] == "Dom Casmurro"


def test_filter_by_autor(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    response = client.get("/livros?autor=machado")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["data"]) == 1
    assert "Machado" in payload["data"][0]["autor"]


def test_filter_by_categoria(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    response = client.get("/livros?categoria=classico")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["data"]) == 2


def test_filter_by_disponivel_true(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    # Mark Dom Casmurro as unavailable
    all_books = client.get("/livros").get_json()["data"]
    dom_id = next(b["id"] for b in all_books if b["titulo"] == "Dom Casmurro")
    client.patch(f"/livros/{dom_id}/disponibilidade", json={"disponivel": False})

    response = client.get("/livros?disponivel=true")
    payload = response.get_json()

    assert response.status_code == 200
    assert all(b["disponivel"] for b in payload["data"])
    assert len(payload["data"]) == 2


def test_filter_by_disponivel_false(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    all_books = client.get("/livros").get_json()["data"]
    dom_id = next(b["id"] for b in all_books if b["titulo"] == "Dom Casmurro")
    client.patch(f"/livros/{dom_id}/disponibilidade", json={"disponivel": False})

    response = client.get("/livros?disponivel=false")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["data"]) == 1
    assert payload["data"][0]["disponivel"] is False


def test_combined_filters(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    response = client.get("/livros?categoria=classico&autor=machado")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["data"]) == 1
    assert payload["data"][0]["titulo"] == "Dom Casmurro"


def test_no_filter_returns_all(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "catalogo.db")})
    client = app.test_client()
    _seed_books(client)

    response = client.get("/livros")
    payload = response.get_json()

    assert response.status_code == 200
    assert len(payload["data"]) == 3

