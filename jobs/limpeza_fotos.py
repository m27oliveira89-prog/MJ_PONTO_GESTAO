from services.foto_service import PHOTO_RETENTION_DAYS, limpar_foto_expirada


def executar_limpeza_fotos(registros, retention_days=PHOTO_RETENTION_DAYS):
    cleaned_count = 0

    for registro in registros:
        if limpar_foto_expirada(registro, retention_days=retention_days):
            cleaned_count += 1

    return {
        "processed_records": len(registros),
        "cleaned_fotos": cleaned_count,
        "retention_days": retention_days,
    }
