"""Business logic for the recommendation service."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests


def fetch_catalog_books(base_url: str) -> List[Dict[str, Any]]:
    """Fetch all books from the catalog service."""
    response = requests.get(f"{base_url}/livros", timeout=3)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success", False):
        message = payload.get("message", "Erro ao consultar o catalogo.")
        raise ValueError(message)
    return payload.get("data", [])


def get_recommendations(categoria: str, base_url: str | None = None) -> List[Dict[str, Any]]:
    """Filter catalog books by category."""
    catalog_url = base_url or os.getenv("CATALOGO_BASE_URL", "http://localhost:5001")
    books = fetch_catalog_books(catalog_url)
    categoria_normalizada = categoria.strip().lower()
    return [
        book
        for book in books
        if str(book.get("categoria", "")).strip().lower() == categoria_normalizada
    ]
