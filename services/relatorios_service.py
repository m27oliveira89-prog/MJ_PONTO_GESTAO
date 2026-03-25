from services.ponto_service import list_registros


def build_relatorio_ponto(filters):
    registros = _apply_filters(list_registros(), filters)

    return {
        "total_registros": len(registros),
        "totais_por_tipo": _count_by_tipo(registros),
        "totais_por_funcionario": _count_by_funcionario(registros),
        "registros": sorted(registros, key=_sort_key, reverse=True),
    }


def _apply_filters(registros, filters):
    funcionario = (filters.get("funcionario") or "").strip().lower()
    data_inicial = (filters.get("data_inicial") or "").strip()
    data_final = (filters.get("data_final") or "").strip()

    filtered_registros = list(registros)

    if funcionario:
        filtered_registros = [
            registro
            for registro in filtered_registros
            if registro.get("funcionario", "").strip().lower() == funcionario
        ]

    if data_inicial:
        filtered_registros = [
            registro
            for registro in filtered_registros
            if registro.get("data", "") >= data_inicial
        ]

    if data_final:
        filtered_registros = [
            registro
            for registro in filtered_registros
            if registro.get("data", "") <= data_final
        ]

    return filtered_registros


def _count_by_tipo(registros):
    totals = {
        "entrada": 0,
        "almoco_saida": 0,
        "retorno": 0,
        "saida_final": 0,
    }

    for registro in registros:
        tipo = registro.get("tipo")
        if tipo in totals:
            totals[tipo] += 1

    return totals


def _count_by_funcionario(registros):
    totals = {}

    for registro in registros:
        funcionario = registro.get("funcionario", "Nao informado")
        totals[funcionario] = totals.get(funcionario, 0) + 1

    return dict(sorted(totals.items(), key=lambda item: item[0].lower()))


def _sort_key(registro):
    return (
        registro.get("data", ""),
        registro.get("hora", ""),
    )
