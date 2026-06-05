"""HTTP routes for the recommendation service."""

from __future__ import annotations

from typing import Any, Dict

import requests
from flask import Blueprint

from .services import get_recommendations

recommendation_bp = Blueprint("recomendacoes", __name__)


def json_response(
    *, success: bool, data: Any | None = None, message: str | None = None, status: int = 200
) -> tuple[Dict[str, Any], int]:
    payload: Dict[str, Any] = {"success": success}
    if success:
        payload["data"] = data
    else:
        payload["message"] = message
    return payload, status


@recommendation_bp.get("/recomendacoes/<categoria>")
def recomendar_livros(categoria: str):
    try:
        recomendacoes = get_recommendations(categoria)
    except requests.RequestException:
        return json_response(
            success=False,
            message="Falha ao comunicar com o servico de catalogo.",
            status=502,
        )
    except ValueError as exc:
        return json_response(success=False, message=str(exc), status=502)

    return json_response(success=True, data=recomendacoes)
