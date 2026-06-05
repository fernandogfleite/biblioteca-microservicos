"""Data models for the catalog service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Book:
    """Represents a book in the catalog."""

    id: str
    titulo: str
    autor: str
    categoria: str
    disponivel: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert the book to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "titulo": self.titulo,
            "autor": self.autor,
            "categoria": self.categoria,
            "disponivel": self.disponivel,
        }
