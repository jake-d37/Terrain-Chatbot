# config.py
import os
from dotenv import load_dotenv


class Config:
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV != "production"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Connect to Firebase (Optional)
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

    # Client's HTTP API(Optional)
    INVENTORY_BASE_URL = os.getenv(
        "INVENTORY_BASE_URL"
    )  # https://partner.example.com/api
    INVENTORY_API_KEY = os.getenv("INVENTORY_API_KEY")


def load_config(app):
    load_dotenv()
    app.config["GENAI_MODEL"] = os.environ.get("GENAI_MODEL", "gemini-1.5-pro")
    app.config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY")
