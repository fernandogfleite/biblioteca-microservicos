"""Flask application for the API Gateway."""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS

from .routes.gateway_routes import gateway_bp


def create_app() -> Flask:
    """Application factory for the API Gateway."""
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(gateway_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
