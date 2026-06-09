"""Flask application for the user service."""

from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask
from flask_cors import CORS

from .routes import user_bp
from .services import init_db


def _log_startup(service_name: str, default_port: int) -> None:
    """Print startup message with the configured port."""
    port = os.getenv("PORT", str(default_port))
    print(f"[startup] {service_name} rodando na porta {port}", flush=True)


def _get_cors_origins() -> list[str] | str:
    """Return allowed CORS origins from the environment."""
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
    """Application factory for the user service."""
    app = Flask(__name__)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app.config["DB_PATH"] = os.getenv(
        "USUARIO_DB_PATH", os.path.join(base_dir, "usuarios.db")
    )

    if config:
        app.config.update(config)

    CORS(app, origins=_get_cors_origins())
    init_db(app.config["DB_PATH"])
    app.register_blueprint(user_bp)
    _log_startup("Servico de Usuarios", 5004)
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5004"))
    app.run(host="0.0.0.0", port=port, debug=False)
