from services.ponto_service import list_registros


def list_historico_ponto(funcionario=None):
    registros = list_registros(funcionario=funcionario)
    return sorted(registros, key=_sort_key, reverse=True)


def filter_historico_ponto(filters):
    funcionario = (filters.get("funcionario") or "").strip()
    data = (filters.get("data") or "").strip()
    tipo = (filters.get("tipo") or "").strip().lower()

    registros = list_historico_ponto(funcionario=funcionario or None)

    if data:
        registros = [
            registro
            for registro in registros
            if registro.get("data") == data
        ]

    if tipo:
        registros = [
            registro
            for registro in registros
            if registro.get("tipo") == tipo
        ]

    return registros


def _sort_key(registro):
    return (
        registro.get("data", ""),
        registro.get("hora", ""),
    )
