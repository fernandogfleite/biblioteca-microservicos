"""Data models for the loan service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Loan:
    """Represents a book loan."""

    id: str
    nome_usuario: str
    livro_id: str
    livro_titulo: str
    status: str
    user_id: Optional[str] = None
    data_emprestimo: Optional[str] = None
    data_devolucao: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the loan to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "nome_usuario": self.nome_usuario,
            "livro_id": self.livro_id,
            "livro_titulo": self.livro_titulo,
            "status": self.status,
            "user_id": self.user_id,
            "data_emprestimo": self.data_emprestimo,
            "data_devolucao": self.data_devolucao,
        }


@dataclass(frozen=True)
class Reservation:
    """Represents a reservation for an unavailable book."""

    id: str
    nome_usuario: str
    livro_id: str
    livro_titulo: str
    status: str
    criado_em: str
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the reservation to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "nome_usuario": self.nome_usuario,
            "livro_id": self.livro_id,
            "livro_titulo": self.livro_titulo,
            "status": self.status,
            "criado_em": self.criado_em,
            "user_id": self.user_id,
        }