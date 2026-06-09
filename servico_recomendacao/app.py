"""Flask application for the recommendation service."""

from __future__ import annotations

import os
from typing import Any, Dict

from dotenv import load_dotenv
from flask import Flask

load_dotenv()
from flask_cors import CORS

from .routes import recommendation_bp


def _log_startup(service_name: str, default_port: int) -> None:
    """Print startup message with the configured port."""
    port = os.getenv("PORT", str(default_port))
    print(f"[startup] {service_name} rodando na porta {port}", flush=True)


def _get_cors_origins() -> list[str] | str:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw.lower() in {"*", "all"}:
        return "*"
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:5000",
        "http://localhost:5173",
        "http://localhost:3000",
    ]


def create_app(config: Dict[str, Any] | None = None) -> Flask:
    """Application factory for the recommendation service."""
    app = Flask(__name__)
    if config:
        app.config.update(config)

    CORS(app, origins=_get_cors_origins())
    app.register_blueprint(recommendation_bp)
    _log_startup("Servico de Recomendacao", 5003)
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5003"))
    app.run(host="0.0.0.0", port=port, debug=False)
