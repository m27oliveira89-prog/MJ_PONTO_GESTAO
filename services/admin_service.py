ADMIN_CONFIG = {
    "usar_gps": False,
    "bloquear_localizacao": False,
    "exigir_foto": False,
    "raio": 100,
    "dias_retencao": 30,
    "latitude_referencia": None,
    "longitude_referencia": None,
}


def get_admin_config():
    return dict(ADMIN_CONFIG)


def get_ponto_rules():
    return {
        "usar_gps": ADMIN_CONFIG["usar_gps"],
        "bloquear_localizacao": ADMIN_CONFIG["bloquear_localizacao"],
        "exigir_foto": ADMIN_CONFIG["exigir_foto"],
        "raio": ADMIN_CONFIG["raio"],
        "latitude_referencia": ADMIN_CONFIG["latitude_referencia"],
        "longitude_referencia": ADMIN_CONFIG["longitude_referencia"],
    }


def update_admin_config(config_data):
    raio = _parse_positive_int(config_data.get("raio"), "raio")
    dias_retencao = _parse_positive_int(
        config_data.get("dias_retencao"),
        "dias de retencao",
    )
    latitude_referencia = _parse_optional_float(
        config_data.get("latitude_referencia"),
        "latitude de referencia",
    )
    longitude_referencia = _parse_optional_float(
        config_data.get("longitude_referencia"),
        "longitude de referencia",
    )

    ADMIN_CONFIG.update(
        {
            "usar_gps": bool(config_data.get("usar_gps")),
            "bloquear_localizacao": bool(config_data.get("bloquear_localizacao")),
            "exigir_foto": bool(config_data.get("exigir_foto")),
            "raio": raio,
            "dias_retencao": dias_retencao,
            "latitude_referencia": latitude_referencia,
            "longitude_referencia": longitude_referencia,
        }
    )

    return get_admin_config()


def _parse_positive_int(value, field_name):
    normalized_value = str(value or "").strip()

    if not normalized_value:
        raise ValueError(f"O campo '{field_name}' e obrigatorio.")

    try:
        parsed_value = int(normalized_value)
    except ValueError as exc:
        raise ValueError(f"O campo '{field_name}' deve ser um numero inteiro.") from exc

    if parsed_value < 0:
        raise ValueError(f"O campo '{field_name}' nao pode ser negativo.")

    return parsed_value


def _parse_optional_float(value, field_name):
    normalized_value = str(value or "").strip().replace(",", ".")

    if not normalized_value:
        return None

    try:
        return float(normalized_value)
    except ValueError as exc:
        raise ValueError(f"O campo '{field_name}' deve ser um numero valido.") from exc
