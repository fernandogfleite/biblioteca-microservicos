"""Flask application for the loan service."""

from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask
from flask_cors import CORS

from .routes import loan_bp
from .services import init_db


def create_app(config: Dict[str, Any] | None = None) -> Flask:
    """Application factory for the loan service."""
    app = Flask(__name__)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app.config["DB_PATH"] = os.getenv(
        "EMPRESTIMOS_DB_PATH", os.path.join(base_dir, "emprestimos.db")
    )

    if config:
        app.config.update(config)

    CORS(app)
    init_db(app.config["DB_PATH"])
    app.register_blueprint(loan_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
