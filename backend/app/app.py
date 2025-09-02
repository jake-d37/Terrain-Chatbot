# app.py
import logging, sys
from flask import Flask, jsonify
from app.config import Config
from app.extensions import cors, configure_logging, init_extensions
from app.utils.errors import register_error_handlers
from app.blueprints.chat.routes import chat_bp
from app.blueprints.health.routes import health_bp
from app.config import load_config


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    load_config(app)
    init_extensions(app)
    app.config.from_object(config_object or Config())

    # Initialise extensions
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    configure_logging(app)
    register_error_handlers(app)

    # Register blueprints: keep only API
    from app.blueprints.chat import bp as chat_bp
    from app.blueprints.health import bp as health_bp

    app.register_blueprint(health_bp, url_prefix="/health")
    app.register_blueprint(chat_bp, url_prefix="/v1")  # Not sure

    # stdout log
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    return app
