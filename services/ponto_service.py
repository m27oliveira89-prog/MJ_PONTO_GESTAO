import json
import os
from datetime import datetime

from services.admin_service import get_ponto_rules
from services.foto_service import salvar_foto_base64
from services.funcionarios_service import get_funcionario
from services.gps_service import validate_gps_rules


REGISTROS_FILE = os.path.join("database", "registros_ponto.json")
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

    return loaded_registros


def _save_registros():
    os.makedirs(os.path.dirname(REGISTROS_FILE), exist_ok=True)

    with open(REGISTROS_FILE, "w", encoding="utf-8") as registros_file:
        json.dump(REGISTROS_PONTO, registros_file, ensure_ascii=False, indent=2)


REGISTROS_PONTO.extend(_load_registros())


def registrar_ponto(tipo, funcionario, latitude=None, longitude=None, foto_url=None):
    tipo_normalizado = tipo.strip().lower()
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

    agora = datetime.now()
    registro = {
        "data": agora.strftime("%Y-%m-%d"),
        "hora": agora.strftime("%H:%M:%S"),
        "timestamp": agora.isoformat(timespec="seconds"),
        "tipo": tipo_normalizado,
        "tipo_label": TIPOS_PONTO[tipo_normalizado],
        "funcionario": funcionario,
        "latitude": latitude,
        "longitude": longitude,
        "foto_url": foto_url,
    }

    REGISTROS_PONTO.append(registro)
    _save_registros()
    return registro


def list_registros(funcionario=None):
    if funcionario:
        registros = [
            registro
            for registro in REGISTROS_PONTO
            if registro["funcionario"] == funcionario
        ]
        return sorted(registros, key=_sort_key, reverse=True)

    return sorted(REGISTROS_PONTO, key=_sort_key, reverse=True)


def registrar_ponto_funcionario(
    matricula,
    tipo,
    foto_base64=None,
    latitude=None,
    longitude=None,
):
    normalized_matricula = (matricula or "").strip()
    normalized_tipo = (tipo or "entrada").strip().lower()

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
        raise ValueError("\u00c9 necess\u00e1rio tirar a foto para registrar o ponto")

    agora = datetime.now()
    foto_url = salvar_foto_base64(
        normalized_foto,
        funcionario.get("nome"),
        timestamp=agora,
    )
    registro = {
        "data": agora.strftime("%Y-%m-%d"),
        "hora": agora.strftime("%H:%M:%S"),
        "timestamp": agora.isoformat(timespec="seconds"),
        "tipo": normalized_tipo,
        "tipo_label": TIPOS_PONTO[normalized_tipo],
        "funcionario": funcionario["nome"],
        "matricula": funcionario["matricula"],
        "cargo": funcionario["cargo"],
        "latitude": normalized_latitude,
        "longitude": normalized_longitude,
        "foto_url": foto_url,
    }

    REGISTROS_PONTO.append(registro)
    _save_registros()
    return registro


def _sort_key(registro):
    return (
        registro.get("timestamp", ""),
        registro.get("data", ""),
        registro.get("hora", ""),
    )
