import csv
from datetime import datetime
from io import BytesIO
from io import StringIO

from services.relatorios_service import build_relatorio_ponto


EXPORT_COLUMNS = (
    ("data", "Data"),
    ("hora", "Hora"),
    ("tipo_label", "Tipo"),
    ("funcionario", "Funcionario"),
)

PDF_PAGE_WIDTH = 595
PDF_PAGE_HEIGHT = 842
PDF_MARGIN_LEFT = 40
PDF_MARGIN_RIGHT = 40
PDF_TOP_Y = 800
PDF_FOOTER_Y = 28
PDF_MIN_TABLE_Y = 80
PDF_TABLE_HEADER_HEIGHT = 20
PDF_TABLE_ROW_HEIGHT = 18
PDF_TABLE_COLUMNS = (
    ("Data", 70),
    ("Entrada", 52),
    ("Saida Almoco", 72),
    ("Retorno", 52),
    ("Saida Final", 62),
    ("Horas Trabalhadas", 86),
    ("Observacao", 111),
)


def exportar_csv(filters):
    relatorio = build_relatorio_ponto(filters)
    rows = _serialize_rows(relatorio["registros"])

    content = _build_csv(rows).encode("utf-8-sig")
    filename = _build_filename("relatorio_ponto", "csv")
    mimetype = "text/csv; charset=utf-8"

    return content, filename, mimetype


def exportar_pdf(filters, current_user=None):
    relatorio = build_relatorio_ponto(filters)
    pdf_content = _build_espelho_pdf(
        relatorio,
        filters,
        current_user=current_user,
    )
    filename = _build_filename("espelho_ponto", "pdf")
    mimetype = "application/pdf"

    return pdf_content, filename, mimetype


def _serialize_rows(registros):
    serialized_rows = []

    for registro in registros:
        serialized_rows.append(
            [
                _format_cell(registro.get(column_name))
                for column_name, _ in EXPORT_COLUMNS
            ]
        )

    return serialized_rows


def _format_cell(value):
    if value is None:
        return ""

    return str(value)


def _build_filename(prefix, extension):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def _build_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([column_label for _, column_label in EXPORT_COLUMNS])

    if rows:
        writer.writerows(rows)
    else:
        writer.writerow(["Nenhum registro encontrado."])

    return output.getvalue()


def _build_espelho_pdf(relatorio, filters, current_user=None):
    emission_datetime = datetime.now()
    sections = _build_sections(relatorio["registros"])
    pages = []

    if not sections:
        page = _new_page(pages)
        _draw_report_title(page)
        page["y"] -= 36
        _draw_info_line(page, "Periodo", _resolve_periodo(filters))
        _draw_info_line(
            page,
            "Data de emissao",
            emission_datetime.strftime("%d/%m/%Y %H:%M"),
        )
        _draw_info_line(page, "Emitido por", _resolve_emissor(current_user))
        page["y"] -= 18
        _draw_text(
            page,
            PDF_MARGIN_LEFT,
            page["y"],
            "Nenhum registro encontrado para o periodo selecionado",
            size=10,
        )
    else:
        for section_index, section in enumerate(sections):
            page = _start_section_page(
                pages,
                section,
                filters,
                emission_datetime,
                current_user=current_user,
                continuation=False,
            )

            for row in section["rows"]:
                if page["y"] - PDF_TABLE_ROW_HEIGHT < PDF_MIN_TABLE_Y:
                    page = _start_section_page(
                        pages,
                        section,
                        filters,
                        emission_datetime,
                        current_user=current_user,
                        continuation=True,
                    )

                _draw_table_row(page, row)

            if section_index < len(sections) - 1:
                page["y"] -= 14

    for index, page in enumerate(pages, start=1):
        _draw_footer(
            page,
            page_number=index,
            total_pages=len(pages),
            emission_datetime=emission_datetime,
        )

    pdf_buffer = BytesIO()
    pdf_buffer.write(_render_paginated_pdf(pages))
    return pdf_buffer.getvalue()


def _build_sections(registros):
    grouped = {}

    for registro in sorted(registros, key=_registro_sort_key):
        funcionario = registro.get("funcionario") or "Nao informado"
        grouped.setdefault(funcionario, []).append(registro)

    sections = []

    for funcionario, employee_records in grouped.items():
        daily_rows = _build_daily_rows(employee_records)
        first_record = employee_records[0] if employee_records else {}
        sections.append(
            {
                "funcionario": funcionario,
                "matricula": first_record.get("matricula") or "--",
                "cargo": first_record.get("cargo") or "--",
                "summary": _build_section_summary(employee_records, daily_rows),
                "rows": daily_rows,
            }
        )

    return sections


def _build_daily_rows(registros):
    grouped_by_date = {}

    for registro in sorted(registros, key=_registro_sort_key):
        grouped_by_date.setdefault(registro.get("data", ""), []).append(registro)

    daily_rows = []

    for data in sorted(grouped_by_date.keys()):
        row = {
            "data": _format_date(data),
            "entrada": "--",
            "almoco_saida": "--",
            "retorno": "--",
            "saida_final": "--",
            "horas_trabalhadas": "--",
            "observacao": "Batidas incompletas",
        }

        registros_do_dia = sorted(grouped_by_date[data], key=lambda item: item.get("hora", ""))

        for registro in registros_do_dia:
            tipo = (registro.get("tipo") or "").strip().lower()
            hora = _normalize_hour(registro.get("hora"))

            if tipo == "entrada" and row["entrada"] == "--":
                row["entrada"] = hora
            elif tipo == "almoco_saida" and row["almoco_saida"] == "--":
                row["almoco_saida"] = hora
            elif tipo == "retorno" and row["retorno"] == "--":
                row["retorno"] = hora
            elif tipo == "saida_final" and row["saida_final"] == "--":
                row["saida_final"] = hora

        worked_minutes = _calculate_worked_minutes(
            row["entrada"],
            row["almoco_saida"],
            row["retorno"],
            row["saida_final"],
        )

        if worked_minutes is not None:
            row["horas_trabalhadas"] = _minutes_to_hhmm(worked_minutes)
            row["observacao"] = "OK"

        daily_rows.append(row)

    return daily_rows


def _build_section_summary(registros, daily_rows):
    total_minutes = 0

    for row in daily_rows:
        if row["horas_trabalhadas"] != "--":
            total_minutes += _hhmm_to_minutes(row["horas_trabalhadas"])

    return {
        "dias_com_registro": len(daily_rows),
        "entradas": _count_tipo(registros, "entrada"),
        "almoco_saida": _count_tipo(registros, "almoco_saida"),
        "retornos": _count_tipo(registros, "retorno"),
        "saidas_finais": _count_tipo(registros, "saida_final"),
        "horas_apuradas": _minutes_to_hhmm(total_minutes) if total_minutes else "--",
    }


def _count_tipo(registros, tipo):
    return sum(1 for registro in registros if registro.get("tipo") == tipo)


def _calculate_worked_minutes(entrada, almoco_saida, retorno, saida_final):
    if "--" in {entrada, almoco_saida, retorno, saida_final}:
        return None

    entrada_min = _time_to_minutes(entrada)
    almoco_saida_min = _time_to_minutes(almoco_saida)
    retorno_min = _time_to_minutes(retorno)
    saida_final_min = _time_to_minutes(saida_final)

    if None in {entrada_min, almoco_saida_min, retorno_min, saida_final_min}:
        return None

    total_minutes = (saida_final_min - entrada_min) - (retorno_min - almoco_saida_min)

    if total_minutes < 0:
        return None

    return total_minutes


def _time_to_minutes(value):
    if not value or value == "--":
        return None

    try:
        parts = value.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
    except (IndexError, ValueError):
        return None

    return (hour * 60) + minute


def _minutes_to_hhmm(minutes):
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours:02d}:{remaining_minutes:02d}"


def _hhmm_to_minutes(value):
    try:
        hours, minutes = value.split(":")
        return (int(hours) * 60) + int(minutes)
    except (ValueError, AttributeError):
        return 0


def _registro_sort_key(registro):
    return (
        registro.get("funcionario", ""),
        registro.get("data", ""),
        registro.get("hora", ""),
    )


def _normalize_hour(value):
    text = _format_cell(value)

    if len(text) >= 5:
        return text[:5]

    return text or "--"


def _format_date(value):
    if not value:
        return "--"

    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


def _resolve_periodo(filters):
    data_inicial = (filters.get("data_inicial") or "").strip()
    data_final = (filters.get("data_final") or "").strip()

    if data_inicial and data_final:
        return f"{_format_date(data_inicial)} a {_format_date(data_final)}"

    if data_inicial:
        return f"A partir de {_format_date(data_inicial)}"

    if data_final:
        return f"Ate {_format_date(data_final)}"

    return "Periodo integral"


def _resolve_emissor(current_user):
    if not current_user:
        return "Nao informado"

    return current_user.get("display_name") or current_user.get("username") or "Nao informado"


def _new_page(pages):
    page = {"commands": [], "y": PDF_TOP_Y}
    pages.append(page)
    return page


def _start_section_page(pages, section, filters, emission_datetime, current_user=None, continuation=False):
    page = _new_page(pages)
    _draw_report_title(page)
    page["y"] -= 36

    _draw_info_line(page, "Funcionario", section["funcionario"])
    _draw_info_line(page, "Matricula", section["matricula"])
    _draw_info_line(page, "Cargo", section["cargo"])
    _draw_info_line(page, "Periodo", _resolve_periodo(filters))
    _draw_info_line(
        page,
        "Data de emissao",
        emission_datetime.strftime("%d/%m/%Y %H:%M"),
    )
    _draw_info_line(page, "Emitido por", _resolve_emissor(current_user))
    page["y"] -= 10

    if continuation:
        _draw_text(page, PDF_MARGIN_LEFT, page["y"], "Continuacao", font="F2", size=9)
        page["y"] -= 18
    else:
        _draw_summary_section(page, section["summary"])

    _draw_table_header(page)
    return page


def _draw_report_title(page):
    title = "ESPELHO DE PONTO"
    _draw_text(page, PDF_MARGIN_LEFT, page["y"], title, font="F2", size=16)
    _draw_line(
        page,
        PDF_MARGIN_LEFT,
        page["y"] - 8,
        PDF_PAGE_WIDTH - PDF_MARGIN_RIGHT,
        page["y"] - 8,
    )


def _draw_info_line(page, label, value):
    _draw_text(page, PDF_MARGIN_LEFT, page["y"], f"{label}: {value}", size=10)
    page["y"] -= 14


def _draw_summary_section(page, summary):
    _draw_text(page, PDF_MARGIN_LEFT, page["y"], "Resumo Geral", font="F2", size=11)
    page["y"] -= 16
    _draw_text(
        page,
        PDF_MARGIN_LEFT,
        page["y"],
        (
            f"Total de dias com registro: {summary['dias_com_registro']}    "
            f"Total de entradas: {summary['entradas']}    "
            f"Saidas para almoco: {summary['almoco_saida']}"
        ),
        size=9,
    )
    page["y"] -= 14
    _draw_text(
        page,
        PDF_MARGIN_LEFT,
        page["y"],
        (
            f"Retornos: {summary['retornos']}    "
            f"Saidas finais: {summary['saidas_finais']}    "
            f"Total de horas apuradas no periodo: {summary['horas_apuradas']}"
        ),
        size=9,
    )
    page["y"] -= 20


def _draw_table_header(page):
    total_width = sum(width for _, width in PDF_TABLE_COLUMNS)
    y_bottom = page["y"] - PDF_TABLE_HEADER_HEIGHT + 4
    _draw_rect(
        page,
        PDF_MARGIN_LEFT,
        y_bottom,
        total_width,
        PDF_TABLE_HEADER_HEIGHT,
        fill_gray=0.92,
        stroke_gray=0.78,
    )

    current_x = PDF_MARGIN_LEFT + 5

    for label, width in PDF_TABLE_COLUMNS:
        _draw_text(page, current_x, page["y"] - 10, label, font="F2", size=8)
        current_x += width

    page["y"] -= PDF_TABLE_HEADER_HEIGHT + 6


def _draw_table_row(page, row):
    total_width = sum(width for _, width in PDF_TABLE_COLUMNS)
    y_bottom = page["y"] - PDF_TABLE_ROW_HEIGHT + 4
    _draw_rect(
        page,
        PDF_MARGIN_LEFT,
        y_bottom,
        total_width,
        PDF_TABLE_ROW_HEIGHT,
        fill_gray=None,
        stroke_gray=0.88,
    )

    row_values = (
        row["data"],
        row["entrada"],
        row["almoco_saida"],
        row["retorno"],
        row["saida_final"],
        row["horas_trabalhadas"],
        row["observacao"],
    )

    current_x = PDF_MARGIN_LEFT + 5

    for value, (_, width) in zip(row_values, PDF_TABLE_COLUMNS):
        _draw_text(
            page,
            current_x,
            page["y"] - 10,
            _truncate_pdf_text(value, width),
            size=8,
        )
        current_x += width

    page["y"] -= PDF_TABLE_ROW_HEIGHT


def _draw_footer(page, page_number, total_pages, emission_datetime):
    footer_text = (
        f"Gerado em {emission_datetime.strftime('%d/%m/%Y %H:%M')}    "
        f"Pagina {page_number} de {total_pages}"
    )
    _draw_line(
        page,
        PDF_MARGIN_LEFT,
        PDF_FOOTER_Y + 12,
        PDF_PAGE_WIDTH - PDF_MARGIN_RIGHT,
        PDF_FOOTER_Y + 12,
    )
    _draw_text(page, PDF_MARGIN_LEFT, PDF_FOOTER_Y, footer_text, size=8)


def _sanitize_pdf_text(value):
    sanitized = str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    sanitized = sanitized.replace("\r", " ").replace("\n", " ")
    return sanitized


def _draw_text(page, x, y, text, font="F1", size=9):
    safe_text = _sanitize_pdf_text(text)
    page["commands"].append(f"BT /{font} {size} Tf 1 0 0 1 {x} {y} Tm ({safe_text}) Tj ET")


def _draw_line(page, x1, y1, x2, y2):
    page["commands"].append(f"0.75 G 0.6 w {x1} {y1} m {x2} {y2} l S 0 G")


def _draw_rect(page, x, y, width, height, fill_gray=None, stroke_gray=0.8):
    commands = []

    if fill_gray is not None:
        commands.append(f"{fill_gray} g {x} {y} {width} {height} re f")

    if stroke_gray is not None:
        commands.append(f"{stroke_gray} G 0.6 w {x} {y} {width} {height} re S 0 G")

    page["commands"].extend(commands)


def _truncate_pdf_text(value, width):
    text = _format_cell(value)
    max_chars = max(8, int((width - 10) / 4.6))

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3].rstrip() + "..."


def _render_paginated_pdf(pages):
    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")

    kids_refs = []
    page_object_start = 3
    content_object_start = page_object_start + len(pages)
    font_regular_id = content_object_start + len(pages)
    font_bold_id = font_regular_id + 1

    for index in range(len(pages)):
        page_object_id = page_object_start + index
        kids_refs.append(f"{page_object_id} 0 R")

    objects.append(
        f"2 0 obj << /Type /Pages /Kids [{' '.join(kids_refs)}] /Count {len(pages)} >> endobj\n".encode("latin-1")
    )

    for index, page in enumerate(pages):
        page_object_id = page_object_start + index
        content_object_id = content_object_start + index
        objects.append(
            (
                f"{page_object_id} 0 obj << /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {PDF_PAGE_WIDTH} {PDF_PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_object_id} 0 R >> endobj\n"
            ).encode("latin-1")
        )

    for index, page in enumerate(pages):
        content_object_id = content_object_start + index
        content_stream = "\n".join(page["commands"]).encode("latin-1", errors="replace")
        objects.append(
            f"{content_object_id} 0 obj << /Length {len(content_stream)} >> stream\n".encode("latin-1")
            + content_stream
            + b"\nendstream endobj\n"
        )

    objects.append(
        f"{font_regular_id} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n".encode("latin-1")
    )
    objects.append(
        f"{font_bold_id} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n".encode("latin-1")
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )

    return bytes(pdf)
