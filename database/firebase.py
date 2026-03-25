import json

import firebase_admin
from firebase_admin import credentials, firestore, storage

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

from config import Config


load_dotenv()


def _build_firebase_options():
    options = {}

    if Config.FIREBASE_PROJECT_ID:
        options["projectId"] = Config.FIREBASE_PROJECT_ID

    if Config.FIREBASE_STORAGE_BUCKET:
        options["storageBucket"] = Config.FIREBASE_STORAGE_BUCKET

    return options


def initialize_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    credentials_json = Config.FIREBASE_CREDENTIALS_JSON

    if not credentials_json:
        raise ValueError("Defina FIREBASE_CREDENTIALS_JSON no ambiente.")

    try:
        credentials_data = json.loads(credentials_json)
    except json.JSONDecodeError as exc:
        raise ValueError("FIREBASE_CREDENTIALS_JSON contem um JSON invalido.") from exc

    credential = credentials.Certificate(credentials_data)
    options = _build_firebase_options()

    return firebase_admin.initialize_app(credential, options or None)


def get_firestore_client():
    app = initialize_firebase()
    return firestore.client(app=app)


def get_storage_bucket():
    app = initialize_firebase()
    return storage.bucket(app=app)
