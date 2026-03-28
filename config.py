import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False


load_dotenv()

DEFAULT_SECRET_KEY = "change-this-secret-in-production"


def _env_flag(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or DEFAULT_SECRET_KEY
    DEBUG = _env_flag("FLASK_DEBUG")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()
