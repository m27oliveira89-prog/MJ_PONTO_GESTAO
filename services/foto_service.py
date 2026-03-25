from datetime import datetime, timedelta


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
