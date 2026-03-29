import json
import os
import uuid
from datetime import datetime

from services.admin_service import get_ponto_rules
from services.foto_service import salvar_foto_base64
from services.funcionarios_service import get_funcionario
from services.gps_service import validate_gps_rules

try:
    from database.firebase import get_firestore_client
except Exception:  # pragma: no cover - fallback seguro quando Firebase nao estiver disponivel
    get_firestore_client = None


REGISTROS_FILE = os.path.join("database", "registros_ponto.json")
REGISTROS_COLLECTION = "registros_ponto"
REGISTROS_PONTO = []

TIPOS_PONTO = {
    "entrada": "Entrada",
    "almoco_saida": "Almoco Saida",
    "retorno": "Retorno",
    "saida_final": "Saida Final",
}


def _load_registros():
    if not os.path.exists(REGISTROS_FILE):
        return []

    try:
        with open(REGISTROS_FILE, "r", encoding="utf-8") as registros_file:
            loaded_registros = json.load(registros_file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(loaded_registros, list):
        return []

    return [_normalize_registro(registro) for registro in loaded_registros]


def _save_registros():
    os.makedirs(os.path.dirname(REGISTROS_FILE), exist_ok=True)

    with open(REGISTROS_FILE, "w", encoding="utf-8") as registros_file:
        json.dump(REGISTROS_PONTO, registros_file, ensure_ascii=False, indent=2)


def registrar_ponto(tipo, funcionario, latitude=None, longitude=None, foto_url=None):
    tipo_normalizado = _normalize_tipo(tipo)
    ponto_rules = get_ponto_rules()

    if tipo_normalizado not in TIPOS_PONTO:
        raise ValueError("Tipo de ponto invalido.")

    if not funcionario:
        raise ValueError("Funcionario nao informado.")

    if ponto_rules["exigir_foto"] and not foto_url:
        raise ValueError("Foto obrigatoria para registrar o ponto.")

    validate_gps_rules(
        latitude=latitude,
        longitude=longitude,
        usar_gps=ponto_rules["usar_gps"],
        bloquear_localizacao=ponto_rules["bloquear_localizacao"],
        raio=ponto_rules["raio"],
        latitude_referencia=ponto_rules["latitude_referencia"],
        longitude_referencia=ponto_rules["longitude_referencia"],
    )

    registro = _build_registro_payload(
        funcionario_data={
            "nome": funcionario,
            "matricula": "",
            "cargo": "",
        },
        tipo=tipo_normalizado,
        latitude=latitude,
        longitude=longitude,
        foto_url=foto_url,
        origem="web",
    )
    return _persist_registro(registro)


def list_registros(funcionario=None):
    registros = _load_combined_registros()

    if funcionario:
        registros = [
            registro
            for registro in registros
            if _matches_funcionario(registro, funcionario)
        ]

    return sorted(registros, key=_sort_key, reverse=True)


def registrar_ponto_funcionario(
    matricula,
    tipo,
    foto_base64=None,
    latitude=None,
    longitude=None,
    origem="web",
):
    normalized_matricula = (matricula or "").strip()
    normalized_tipo = _normalize_tipo(tipo)

    if not normalized_matricula:
        raise ValueError("Selecione um funcionario para bater o ponto.")

    if normalized_tipo not in TIPOS_PONTO:
        raise ValueError("Selecione o tipo de ponto.")

    funcionario = get_funcionario(normalized_matricula)

    if not funcionario:
        raise ValueError("Funcionario nao encontrado.")

    if funcionario.get("status") != "ativo":
        raise ValueError("Somente funcionarios ativos podem bater ponto.")

    normalized_foto = (foto_base64 or "").strip()
    normalized_latitude = (latitude or "").strip()
    normalized_longitude = (longitude or "").strip()

    if not normalized_latitude or not normalized_longitude:
        raise ValueError("Ative o GPS do seu dispositivo para registrar o ponto")

    if not normalized_foto:
        raise ValueError("É necessário tirar a foto para registrar o ponto")

    agora = datetime.now()
    foto_url = salvar_foto_base64(
        normalized_foto,
        funcionario.get("nome"),
        timestamp=agora,
    )
    registro = _build_registro_payload(
        funcionario_data=funcionario,
        tipo=normalized_tipo,
        latitude=normalized_latitude,
        longitude=normalized_longitude,
        foto_url=foto_url,
        origem=origem,
        timestamp=agora,
    )

    return _persist_registro(registro)


def _build_registro_payload(
    funcionario_data,
    tipo,
    latitude=None,
    longitude=None,
    foto_url=None,
    origem="web",
    timestamp=None,
):
    agora = timestamp or datetime.now()
    matricula = (funcionario_data.get("matricula") or "").strip()
    nome_funcionario = (
        funcionario_data.get("nome")
        or funcionario_data.get("funcionario")
        or "Nao informado"
    ).strip()

    registro = {
        "registro_id": uuid.uuid4().hex,
        "funcionario_id": matricula or nome_funcionario.lower().replace(" ", "_"),
        "funcionario": nome_funcionario,
        "nome_funcionario": nome_funcionario,
        "matricula": matricula,
        "cargo": (funcionario_data.get("cargo") or "").strip(),
        "data": agora.strftime("%Y-%m-%d"),
        "hora": agora.strftime("%H:%M:%S"),
        "timestamp": agora.isoformat(timespec="seconds"),
        "tipo": tipo,
        "tipo_label": TIPOS_PONTO[tipo],
        "latitude": _normalize_optional_value(latitude),
        "longitude": _normalize_optional_value(longitude),
        "foto_url": _normalize_optional_value(foto_url),
        "origem_registro": (origem or "web").strip().lower() or "web",
        "status": "valido",
    }

    return _normalize_registro(registro)


def _persist_registro(registro):
    normalized_registro = _normalize_registro(registro)
    _upsert_local_registro(normalized_registro)
    _save_registros()
    _save_registro_firestore(normalized_registro)
    return normalized_registro


def _upsert_local_registro(registro):
    registro_id = registro.get("registro_id")

    for index, current in enumerate(REGISTROS_PONTO):
        if current.get("registro_id") == registro_id:
            REGISTROS_PONTO[index] = registro
            return

    REGISTROS_PONTO.append(registro)


def _load_combined_registros():
    local_registros = [_normalize_registro(registro) for registro in REGISTROS_PONTO]
    firestore_registros = _load_firestore_registros()
    registros_unificados = {}

    for registro in local_registros + firestore_registros:
        normalized = _normalize_registro(registro)
        if normalized.get("status") != "valido":
            continue

        registros_unificados[_registro_identity(normalized)] = normalized

    return list(registros_unificados.values())


def _load_firestore_registros():
    client = _get_firestore_client_safe()

    if client is None:
        return []

    try:
        documentos = client.collection(REGISTROS_COLLECTION).stream()
    except Exception:
        return []

    registros = []

    for documento in documentos:
        data = documento.to_dict() or {}
        if not isinstance(data, dict):
            continue

        data.setdefault("registro_id", documento.id)
        registros.append(_normalize_registro(data))

    return registros


def _save_registro_firestore(registro):
    client = _get_firestore_client_safe()

    if client is None:
        return

    try:
        client.collection(REGISTROS_COLLECTION).document(
            registro["registro_id"]
        ).set(registro)
    except Exception:
        return


def _get_firestore_client_safe():
    if get_firestore_client is None:
        return None

    try:
        return get_firestore_client()
    except Exception:
        return None


def _normalize_registro(registro):
    if not isinstance(registro, dict):
        return {}

    normalized_tipo = _normalize_tipo(registro.get("tipo"))
    timestamp = _normalize_timestamp(
        registro.get("timestamp"),
        registro.get("data"),
        registro.get("hora"),
    )
    data = _normalize_data(registro.get("data"), timestamp)
    hora = _normalize_hora(registro.get("hora"), timestamp)
    nome_funcionario = (
        registro.get("nome_funcionario")
        or registro.get("funcionario")
        or "Nao informado"
    )
    matricula = (registro.get("matricula") or "").strip()
    funcionario_id = (
        registro.get("funcionario_id")
        or matricula
        or nome_funcionario.strip().lower().replace(" ", "_")
    )
    registro_id = (
        registro.get("registro_id")
        or registro.get("id")
        or _build_fallback_registro_id(
            funcionario_id=funcionario_id,
            timestamp=timestamp,
            tipo=normalized_tipo,
        )
    )

    return {
        "registro_id": registro_id,
        "funcionario_id": funcionario_id,
        "funcionario": nome_funcionario.strip() or "Nao informado",
        "nome_funcionario": nome_funcionario.strip() or "Nao informado",
        "matricula": matricula,
        "cargo": (registro.get("cargo") or "").strip(),
        "data": data,
        "hora": hora,
        "timestamp": timestamp,
        "tipo": normalized_tipo,
        "tipo_label": TIPOS_PONTO.get(normalized_tipo, "Nao informado"),
        "latitude": _normalize_optional_value(registro.get("latitude")),
        "longitude": _normalize_optional_value(registro.get("longitude")),
        "foto_url": _normalize_optional_value(registro.get("foto_url")),
        "origem_registro": (registro.get("origem_registro") or registro.get("origem") or "web").strip().lower() or "web",
        "status": (registro.get("status") or "valido").strip().lower() or "valido",
    }


def _normalize_timestamp(timestamp, data=None, hora=None):
    if hasattr(timestamp, "isoformat"):
        return timestamp.isoformat(timespec="seconds")

    normalized_timestamp = (timestamp or "").strip()

    if normalized_timestamp:
        return normalized_timestamp

    normalized_data = (data or "").strip()
    normalized_hora = (hora or "").strip()

    if normalized_data and normalized_hora:
        return f"{normalized_data}T{normalized_hora}"

    return datetime.now().isoformat(timespec="seconds")


def _normalize_data(data, timestamp):
    normalized_data = (data or "").strip()

    if normalized_data:
        return normalized_data

    return timestamp.split("T", 1)[0]


def _normalize_hora(hora, timestamp):
    normalized_hora = (hora or "").strip()

    if normalized_hora:
        return normalized_hora

    if "T" in timestamp:
        return timestamp.split("T", 1)[1][:8]

    return ""


def _normalize_tipo(tipo):
    normalized_tipo = (tipo or "").strip().lower()

    aliases = {
        "almoco saida": "almoco_saida",
        "almoço saída": "almoco_saida",
        "almoço saida": "almoco_saida",
        "saida almoco": "almoco_saida",
        "saída almoço": "almoco_saida",
        "saida_final": "saida_final",
        "saída final": "saida_final",
    }

    return aliases.get(normalized_tipo, normalized_tipo)


def _normalize_optional_value(value):
    normalized_value = (str(value).strip() if value is not None else "")
    return normalized_value or None


def _matches_funcionario(registro, funcionario):
    normalized_target = (funcionario or "").strip().lower()

    if not normalized_target:
        return True

    valores = {
        (registro.get("funcionario") or "").strip().lower(),
        (registro.get("nome_funcionario") or "").strip().lower(),
        (registro.get("matricula") or "").strip().lower(),
        (registro.get("funcionario_id") or "").strip().lower(),
    }

    return normalized_target in valores


def _build_fallback_registro_id(funcionario_id, timestamp, tipo):
    return f"{funcionario_id}_{timestamp}_{tipo}".replace(":", "").replace("-", "")


def _registro_identity(registro):
    return registro.get("registro_id") or _build_fallback_registro_id(
        funcionario_id=registro.get("funcionario_id") or registro.get("matricula") or "",
        timestamp=registro.get("timestamp") or "",
        tipo=registro.get("tipo") or "",
    )


def _sort_key(registro):
    return (
        registro.get("timestamp", ""),
        registro.get("data", ""),
        registro.get("hora", ""),
    )


REGISTROS_PONTO.extend(_load_registros())
