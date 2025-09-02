# extensions.py —— 只保留 API 必需 + 日志 + （可选）Firebase
from flask_cors import CORS
import structlog
import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from flask_cors import CORS


# backend/app/extensions.py
try:
    from flask_cors import CORS
except ImportError:
    CORS = None  # 允许在未安装时跳过


def init_extensions(app):
    if CORS:
        CORS(app, resources={r"/*": {"origins": "*"}})


def init_extensions(app: Flask):
    CORS(app, resources={r"/*": {"origins": "*"}})


cors = CORS()


def configure_logging(app):
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))
    app.logger.info("logging configured")


def get_firestore_client():
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not creds_path or not project_id:
        return None
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate(creds_path), {"projectId": project_id}
        )
    return firestore.client()
