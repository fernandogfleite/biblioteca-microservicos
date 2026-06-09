"""Tests for authentication (login endpoint in user service)."""

from __future__ import annotations

import os

import jwt
import pytest

from servico_usuario.app import create_app

SECRET = "test-secret"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    app = create_app({"TESTING": True, "DB_PATH": str(tmp_path / "usuarios.db")})
    client = app.test_client()

    client.post(
        "/usuarios",
        json={
            "full_name": "Teste User",
            "email": "user@example.com",
            "cpf": "12345678901",
            "password": "senha123",
        },
    )
    client.post(
        "/usuarios",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "cpf": "98765432100",
            "password": "admin123",
            "role": "ADMIN",
        },
    )
    return client


def test_login_success_user(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "senha123"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert "token" in payload["data"]
    assert payload["data"]["user"]["role"] == "USER"


def test_login_success_admin(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["user"]["role"] == "ADMIN"


def test_login_wrong_password(client):
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_login_unknown_email(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "senha123"},
    )

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_login_missing_fields(client):
    response = client.post("/auth/login", json={"email": "user@example.com"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_jwt_token_structure(client, monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "senha123"},
    )
    token = response.get_json()["data"]["token"]

    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert "user_id" in claims
    assert "email" in claims
    assert "role" in claims
    assert claims["role"] == "USER"
    assert claims["email"] == "user@example.com"
