"""Data models for the user service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


ROLE_ADMIN = "ADMIN"
ROLE_USER = "USER"
VALID_ROLES = {ROLE_ADMIN, ROLE_USER}


@dataclass(frozen=True)
class User:
    """Represents a system user."""

    id: str
    full_name: str
    email: str
    cpf: str
    role: str
    password_hash: str
    created_at: str

    def to_dict(self, include_password_hash: bool = False) -> Dict[str, Any]:
        """Convert the user to a JSON-serializable dictionary."""
        data: Dict[str, Any] = {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "cpf": self.cpf,
            "role": self.role,
            "created_at": self.created_at,
        }
        if include_password_hash:
            data["password_hash"] = self.password_hash
        return data
