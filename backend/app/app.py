# app.py
import logging, sys
from flask import Flask, jsonify
from app.config import Config
from app.extensions import init_extensions, configure_logging
from app.utils.errors import register_error_handlers
from app.blueprints.chat.routes import chat_bp
from app.blueprints.health.routes import health_bp
from app.config import load_config


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    # Ensure JSON responses are UTF-8 and do not escape non-ASCII characters
    app.config["JSON_AS_ASCII"] = False  # legacy key for older Werkzeug/Flask
    try:
        # Flask 2.3+/3.x JSON provider
        app.json.ensure_ascii = False
    except Exception:
        pass
    load_config(app)
    init_extensions(app)
    app.config.from_object(config_object or Config())

    configure_logging(app)
    register_error_handlers(app)

    # Register blueprints
    from app.blueprints.chat.routes import chat_bp
    from app.blueprints.health.routes import health_bp

    app.register_blueprint(health_bp, url_prefix="/health")
    app.register_blueprint(chat_bp, url_prefix="/v1")

    return app
