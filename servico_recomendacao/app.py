"""Flask application for the recommendation service."""

from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask
from flask_cors import CORS

from .routes import recommendation_bp


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
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5003"))
    app.run(host="0.0.0.0", port=port, debug=False)
