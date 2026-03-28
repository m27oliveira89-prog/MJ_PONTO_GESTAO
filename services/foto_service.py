import base64
import binascii
import os
import re
import uuid
from datetime import datetime, timedelta


PHOTO_UPLOAD_FOLDER = os.path.join("static", "uploads", "fotos_ponto")


PHOTO_RETENTION_DAYS = 90


def normalize_foto_url(foto_url):
    normalized_foto_url = (foto_url or "").strip()

    if not normalized_foto_url:
        return None

    return normalized_foto_url


def is_foto_expirada(data_registro, retention_days=PHOTO_RETENTION_DAYS):
    if not data_registro:
        return False

    try:
        registro_date = datetime.strptime(data_registro, "%Y-%m-%d").date()
    except ValueError:
        return False

    expiration_date = datetime.now().date() - timedelta(days=retention_days)
    return registro_date <= expiration_date


def limpar_foto_expirada(registro, retention_days=PHOTO_RETENTION_DAYS):
    if not registro.get("foto_url"):
        return False

    if not is_foto_expirada(registro.get("data"), retention_days=retention_days):
        return False

    registro["foto_url"] = None
    return True


def salvar_foto_base64(image_data_url, funcionario_nome, timestamp=None):
    normalized_foto_url = normalize_foto_url(image_data_url)

    if not normalized_foto_url:
        raise ValueError("\u00c9 necess\u00e1rio tirar a foto para registrar o ponto")

    if "," not in normalized_foto_url:
        raise ValueError("Formato de imagem invalido para registro do ponto.")

    header, encoded_data = normalized_foto_url.split(",", 1)

    if "image/jpeg" not in header and "image/jpg" not in header:
        raise ValueError("Formato de imagem invalido para registro do ponto.")

    try:
        image_bytes = base64.b64decode(encoded_data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Formato de imagem invalido para registro do ponto.") from exc

    target_timestamp = timestamp or datetime.now()
    safe_name = _slugify(funcionario_nome or "funcionario")
    file_name = (
        f"{safe_name}_{target_timestamp.strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid.uuid4().hex[:8]}.jpg"
    )
    os.makedirs(PHOTO_UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(PHOTO_UPLOAD_FOLDER, file_name)

    with open(file_path, "wb") as image_file:
        image_file.write(image_bytes)

    return "/" + file_path.replace("\\", "/")


def _slugify(value):
    normalized_value = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized_value = normalized_value.strip("_")
    return normalized_value or "funcionario"
