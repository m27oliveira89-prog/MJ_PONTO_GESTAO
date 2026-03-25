from math import atan2, cos, radians, sin, sqrt


def parse_coordinates(latitude, longitude):
    parsed_latitude = _to_float(latitude, "latitude")
    parsed_longitude = _to_float(longitude, "longitude")

    return {
        "latitude": parsed_latitude,
        "longitude": parsed_longitude,
    }


def validate_gps_rules(
    latitude,
    longitude,
    usar_gps=False,
    bloquear_localizacao=False,
    raio=None,
    latitude_referencia=None,
    longitude_referencia=None,
):
    if usar_gps and (latitude is None or longitude is None):
        raise ValueError("GPS obrigatorio para registrar o ponto.")

    if not bloquear_localizacao:
        return

    if latitude is None or longitude is None:
        raise ValueError("Localizacao obrigatoria para validar o ponto.")

    if latitude_referencia is None or longitude_referencia is None:
        raise ValueError("Localizacao de referencia nao configurada pelo admin.")

    if raio is None:
        raise ValueError("Raio de validacao nao configurado pelo admin.")

    distance_in_meters = calculate_distance_meters(
        latitude,
        longitude,
        latitude_referencia,
        longitude_referencia,
    )

    if distance_in_meters > raio:
        raise ValueError("Localizacao fora do raio permitido para registro.")


def calculate_distance_meters(
    latitude,
    longitude,
    latitude_referencia,
    longitude_referencia,
):
    earth_radius_in_meters = 6371000

    latitude_rad = radians(latitude)
    longitude_rad = radians(longitude)
    latitude_ref_rad = radians(latitude_referencia)
    longitude_ref_rad = radians(longitude_referencia)

    delta_latitude = latitude_ref_rad - latitude_rad
    delta_longitude = longitude_ref_rad - longitude_rad

    haversine = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_rad) * cos(latitude_ref_rad) * sin(delta_longitude / 2) ** 2
    )
    central_angle = 2 * atan2(sqrt(haversine), sqrt(1 - haversine))

    return earth_radius_in_meters * central_angle


def _to_float(value, field_name):
    normalized_value = (value or "").strip()

    if not normalized_value:
        return None

    normalized_value = normalized_value.replace(",", ".")

    try:
        return float(normalized_value)
    except ValueError as exc:
        raise ValueError(f"{field_name.capitalize()} invalida.") from exc
