"""Data models for the loan service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Loan:
    """Represents a book loan."""

    id: str
    nome_usuario: str
    livro_id: str
    livro_titulo: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert the loan to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "nome_usuario": self.nome_usuario,
            "livro_id": self.livro_id,
            "livro_titulo": self.livro_titulo,
            "status": self.status,
        }
