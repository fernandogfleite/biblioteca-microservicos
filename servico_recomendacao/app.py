"""Flask application for the recommendation service."""

from __future__ import annotations

from typing import Any, Dict

from flask import Flask
from flask_cors import CORS

from .routes import recommendation_bp


def create_app(config: Dict[str, Any] | None = None) -> Flask:
    """Application factory for the recommendation service."""
    app = Flask(__name__)
    if config:
        app.config.update(config)

    CORS(app)
    app.register_blueprint(recommendation_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
