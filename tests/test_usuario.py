"""Tests for the user service."""

from __future__ import annotations

from servico_usuario.app import create_app
from servico_usuario.services import authenticate_user, create_user


def test_user_creation(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    response = client.post(
        "/usuarios",
        json={
            "full_name": "Ana Lima",
            "email": "ana@example.com",
            "cpf": "12345678901",
            "password": "senha123",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["full_name"] == "Ana Lima"
    assert data["email"] == "ana@example.com"
    assert data["role"] == "USER"
    assert "password_hash" not in data


def test_user_creation_admin_role(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    response = client.post(
        "/usuarios",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "cpf": "98765432100",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["role"] == "ADMIN"


def test_user_creation_duplicate_email(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    client.post(
        "/usuarios",
        json={
            "full_name": "Ana Lima",
            "email": "dup@example.com",
            "cpf": "11111111111",
            "password": "senha123",
        },
    )

    response = client.post(
        "/usuarios",
        json={
            "full_name": "Outro Nome",
            "email": "dup@example.com",
            "cpf": "22222222222",
            "password": "outrasenha",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_user_creation_duplicate_cpf(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    client.post(
        "/usuarios",
        json={
            "full_name": "Ana Lima",
            "email": "a@example.com",
            "cpf": "33333333333",
            "password": "senha123",
        },
    )

    response = client.post(
        "/usuarios",
        json={
            "full_name": "Outro Nome",
            "email": "b@example.com",
            "cpf": "33333333333",
            "password": "outrasenha",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_user_listing(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    for i in range(3):
        client.post(
            "/usuarios",
            json={
                "full_name": f"User {i}",
                "email": f"user{i}@example.com",
                "cpf": f"1234567890{i}",
                "password": "senha123",
            },
        )

    response = client.get("/usuarios")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert len(payload["data"]) == 3


def test_get_user_by_id(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    created = client.post(
        "/usuarios",
        json={
            "full_name": "Carlos Silva",
            "email": "carlos@example.com",
            "cpf": "55555555555",
            "password": "senha123",
        },
    )
    user_id = created.get_json()["data"]["id"]

    response = client.get(f"/usuarios/{user_id}")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["id"] == user_id


def test_get_user_not_found(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    response = client.get("/usuarios/nonexistent-id")
    assert response.status_code == 404
    assert response.get_json()["success"] is False


def test_update_user(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    created = client.post(
        "/usuarios",
        json={
            "full_name": "Carlos Silva",
            "email": "carlos2@example.com",
            "cpf": "66666666666",
            "password": "senha123",
        },
    )
    user_id = created.get_json()["data"]["id"]

    response = client.put(
        f"/usuarios/{user_id}",
        json={"full_name": "Carlos Atualizado"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["full_name"] == "Carlos Atualizado"


def test_delete_user(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    created = client.post(
        "/usuarios",
        json={
            "full_name": "Para Deletar",
            "email": "delete@example.com",
            "cpf": "77777777777",
            "password": "senha123",
        },
    )
    user_id = created.get_json()["data"]["id"]

    response = client.delete(f"/usuarios/{user_id}")
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    get_response = client.get(f"/usuarios/{user_id}")
    assert get_response.status_code == 404


def test_invalid_cpf_format(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    response = client.post(
        "/usuarios",
        json={
            "full_name": "Invalid CPF",
            "email": "inv@example.com",
            "cpf": "123",
            "password": "senha123",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_invalid_role(tmp_path):
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    response = client.post(
        "/usuarios",
        json={
            "full_name": "Bad Role",
            "email": "bad@example.com",
            "cpf": "88888888888",
            "password": "senha123",
            "role": "SUPERUSER",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False
