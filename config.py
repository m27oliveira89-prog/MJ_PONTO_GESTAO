import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False


load_dotenv()


def _env_flag(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_secret_key():
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError("Defina a variavel de ambiente SECRET_KEY.")

    return secret_key


class Config:
    SECRET_KEY = _resolve_secret_key()
    DEBUG = _env_flag("FLASK_DEBUG")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
    FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "").strip()
