from datetime import datetime

from services.admin_service import get_ponto_rules
from services.funcionarios_service import get_funcionario
from services.gps_service import validate_gps_rules


REGISTROS_PONTO = []

TIPOS_PONTO = {
    "entrada": "Entrada",
    "almoco_saida": "Almoco Saida",
    "retorno": "Retorno",
    "saida_final": "Saida Final",
}


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
        "tipo": tipo_normalizado,
        "tipo_label": TIPOS_PONTO[tipo_normalizado],
        "funcionario": funcionario,
        "latitude": latitude,
        "longitude": longitude,
        "foto_url": foto_url,
    }

    REGISTROS_PONTO.append(registro)
    return registro


def list_registros(funcionario=None):
    if funcionario:
        return [
            registro
            for registro in REGISTROS_PONTO
            if registro["funcionario"] == funcionario
        ]

    return list(REGISTROS_PONTO)


def registrar_ponto_funcionario(matricula):
    normalized_matricula = (matricula or "").strip()

    if not normalized_matricula:
        raise ValueError("Selecione um funcionario para bater o ponto.")

    funcionario = get_funcionario(normalized_matricula)

    if not funcionario:
        raise ValueError("Funcionario nao encontrado.")

    if funcionario.get("status") != "ativo":
        raise ValueError("Somente funcionarios ativos podem bater ponto.")

    agora = datetime.now()
    registro = {
        "data": agora.strftime("%Y-%m-%d"),
        "hora": agora.strftime("%H:%M:%S"),
        "tipo": "entrada",
        "tipo_label": "Entrada",
        "funcionario": funcionario["nome"],
        "matricula": funcionario["matricula"],
        "cargo": funcionario["cargo"],
        "latitude": None,
        "longitude": None,
        "foto_url": None,
    }

    REGISTROS_PONTO.append(registro)
    return registro
