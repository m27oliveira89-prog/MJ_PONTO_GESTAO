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
PDF_MIN_TABLE_Y = 92
PDF_TABLE_HEADER_HEIGHT = 26
PDF_TABLE_ROW_HEIGHT = 24
PDF_TABLE_COLUMNS = (
    ("Data", 72),
    ("Entrada", 54),
    ("Saida Almoco", 76),
    ("Retorno", 54),
    ("Saida Final", 66),
    ("Horas Trabalhadas", 94),
    ("Observacao", 99),
)

PDF_COLOR_BLACK = 0
PDF_COLOR_DARK = 0.15
PDF_COLOR_MID = 0.35
PDF_COLOR_LIGHT = 0.92
PDF_COLOR_HEADER_FILL = 0.82
PDF_COLOR_SUMMARY_FILL = 0.94
PDF_COLOR_ALT_ROW_FILL = 0.965
PDF_LINE_STRONG = 1.2
PDF_LINE_NORMAL = 0.9
PDF_LINE_THIN = 0.6


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
        page["y"] -= 40
        _draw_info_line(page, "Periodo", _resolve_periodo(filters))
        _draw_info_line(
            page,
            "Data de emissao",
            emission_datetime.strftime("%d/%m/%Y %H:%M"),
        )
        _draw_info_line(page, "Emitido por", _resolve_emissor(current_user))
        page["y"] -= 18
        _draw_empty_box(
            page,
            "Nenhum registro encontrado para o periodo selecionado.",
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

            for row_index, row in enumerate(section["rows"]):
                if page["y"] - PDF_TABLE_ROW_HEIGHT < PDF_MIN_TABLE_Y:
                    page = _start_section_page(
                        pages,
                        section,
                        filters,
                        emission_datetime,
                        current_user=current_user,
                        continuation=True,
                    )
                    row_index = 0

                _draw_table_row(page, row, is_alt_row=(row_index % 2 == 1))

            if section_index < len(sections) - 1:
                page["y"] -= 16

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

        registros_do_dia = sorted(
            grouped_by_date[data],
            key=lambda item: item.get("hora", ""),
        )

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

    total_minutes = (saida_final_min - entrada_min) - (
        retorno_min - almoco_saida_min
    )

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

    return (
        current_user.get("display_name")
        or current_user.get("username")
        or "Nao informado"
    )


def _new_page(pages):
    page = {"commands": [], "y": PDF_TOP_Y}
    pages.append(page)
    return page


def _start_section_page(
    pages,
    section,
    filters,
    emission_datetime,
    current_user=None,
    continuation=False,
):
    page = _new_page(pages)
    _draw_report_title(page)
    page["y"] -= 38

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
        _draw_text(
            page,
            PDF_MARGIN_LEFT,
            page["y"],
            "CONTINUACAO DO ESPELHO DE PONTO",
            font="F2",
            size=9,
        )
        page["y"] -= 18
    else:
        _draw_summary_section(page, section["summary"])

    _draw_table_header(page)
    return page


def _draw_report_title(page):
    title = "ESPELHO DE PONTO"
    _draw_text(page, PDF_MARGIN_LEFT, page["y"], title, font="F2", size=17)
    _draw_line(
        page,
        PDF_MARGIN_LEFT,
        page["y"] - 10,
        PDF_PAGE_WIDTH - PDF_MARGIN_RIGHT,
        page["y"] - 10,
        gray=PDF_COLOR_BLACK,
        width=PDF_LINE_STRONG,
    )


def _draw_info_line(page, label, value):
    _draw_text(page, PDF_MARGIN_LEFT, page["y"], f"{label}:", font="F2", size=9)
    _draw_text(page, PDF_MARGIN_LEFT + 74, page["y"], value, size=9)
    page["y"] -= 14


def _draw_summary_section(page, summary):
    summary_width = PDF_PAGE_WIDTH - PDF_MARGIN_LEFT - PDF_MARGIN_RIGHT
    summary_height = 54
    y_bottom = page["y"] - summary_height + 6

    _draw_rect(
        page,
        PDF_MARGIN_LEFT,
        y_bottom,
        summary_width,
        summary_height,
        fill_gray=PDF_COLOR_SUMMARY_FILL,
        stroke_gray=PDF_COLOR_BLACK,
        stroke_width=PDF_LINE_STRONG,
    )
    _draw_text(
        page,
        PDF_MARGIN_LEFT + 10,
        page["y"] - 10,
        "RESUMO GERAL",
        font="F2",
        size=10,
    )
    _draw_text(
        page,
        PDF_MARGIN_LEFT + 10,
        page["y"] - 25,
        (
            f"Dias com registro: {summary['dias_com_registro']}    "
            f"Entradas: {summary['entradas']}    "
            f"Saidas almoco: {summary['almoco_saida']}"
        ),
        size=9,
    )
    _draw_text(
        page,
        PDF_MARGIN_LEFT + 10,
        page["y"] - 39,
        (
            f"Retornos: {summary['retornos']}    "
            f"Saidas finais: {summary['saidas_finais']}    "
            f"Horas apuradas: {summary['horas_apuradas']}"
        ),
        size=9,
    )
    page["y"] -= summary_height + 10


def _draw_empty_box(page, message):
    box_width = PDF_PAGE_WIDTH - PDF_MARGIN_LEFT - PDF_MARGIN_RIGHT
    box_height = 34
    y_bottom = page["y"] - box_height + 8
    _draw_rect(
        page,
        PDF_MARGIN_LEFT,
        y_bottom,
        box_width,
        box_height,
        fill_gray=PDF_COLOR_LIGHT,
        stroke_gray=PDF_COLOR_BLACK,
        stroke_width=PDF_LINE_NORMAL,
    )
    _draw_text(page, PDF_MARGIN_LEFT + 10, page["y"] - 12, message, size=10)
    page["y"] -= box_height + 4


def _draw_table_header(page):
    total_width = sum(width for _, width in PDF_TABLE_COLUMNS)
    y_bottom = page["y"] - PDF_TABLE_HEADER_HEIGHT + 5
    _draw_rect(
        page,
        PDF_MARGIN_LEFT,
        y_bottom,
        total_width,
        PDF_TABLE_HEADER_HEIGHT,
        fill_gray=PDF_COLOR_HEADER_FILL,
        stroke_gray=PDF_COLOR_BLACK,
        stroke_width=PDF_LINE_STRONG,
    )

    current_x = PDF_MARGIN_LEFT

    for label, width in PDF_TABLE_COLUMNS:
        _draw_vertical_line(
            page,
            current_x,
            y_bottom,
            y_bottom + PDF_TABLE_HEADER_HEIGHT,
            gray=PDF_COLOR_BLACK,
            width=PDF_LINE_NORMAL,
        )
        _draw_text(
            page,
            current_x + 4,
            page["y"] - 12,
            _truncate_pdf_text(label, width),
            font="F2",
            size=8,
        )
        current_x += width

    _draw_vertical_line(
        page,
        PDF_MARGIN_LEFT + total_width,
        y_bottom,
        y_bottom + PDF_TABLE_HEADER_HEIGHT,
        gray=PDF_COLOR_BLACK,
        width=PDF_LINE_NORMAL,
    )

    page["y"] -= PDF_TABLE_HEADER_HEIGHT + 6


def _draw_table_row(page, row, is_alt_row=False):
    total_width = sum(width for _, width in PDF_TABLE_COLUMNS)
    y_bottom = page["y"] - PDF_TABLE_ROW_HEIGHT + 5
    fill_gray = PDF_COLOR_ALT_ROW_FILL if is_alt_row else None

    _draw_rect(
        page,
        PDF_MARGIN_LEFT,
        y_bottom,
        total_width,
        PDF_TABLE_ROW_HEIGHT,
        fill_gray=fill_gray,
        stroke_gray=PDF_COLOR_BLACK,
        stroke_width=PDF_LINE_NORMAL,
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

    current_x = PDF_MARGIN_LEFT

    for value, (_, width) in zip(row_values, PDF_TABLE_COLUMNS):
        _draw_vertical_line(
            page,
            current_x,
            y_bottom,
            y_bottom + PDF_TABLE_ROW_HEIGHT,
            gray=PDF_COLOR_BLACK,
            width=PDF_LINE_THIN,
        )
        _draw_text(
            page,
            current_x + 4,
            page["y"] - 13,
            _truncate_pdf_text(value, width),
            size=8.5,
        )
        current_x += width

    _draw_vertical_line(
        page,
        PDF_MARGIN_LEFT + total_width,
        y_bottom,
        y_bottom + PDF_TABLE_ROW_HEIGHT,
        gray=PDF_COLOR_BLACK,
        width=PDF_LINE_THIN,
    )

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
        gray=PDF_COLOR_BLACK,
        width=PDF_LINE_NORMAL,
    )
    _draw_text(
        page,
        PDF_MARGIN_LEFT,
        PDF_FOOTER_Y,
        footer_text,
        size=8,
    )


def _sanitize_pdf_text(value):
    sanitized = (
        str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    )
    sanitized = sanitized.replace("\r", " ").replace("\n", " ")
    return sanitized


def _draw_text(page, x, y, text, font="F1", size=9):
    safe_text = _sanitize_pdf_text(text)
    page["commands"].append(
        f"BT 0 g /{font} {size} Tf 1 0 0 1 {x} {y} Tm ({safe_text}) Tj ET"
    )


def _draw_line(page, x1, y1, x2, y2, gray=PDF_COLOR_DARK, width=PDF_LINE_NORMAL):
    page["commands"].append(f"{gray} G {width} w {x1} {y1} m {x2} {y2} l S")


def _draw_vertical_line(page, x, y1, y2, gray=PDF_COLOR_BLACK, width=PDF_LINE_THIN):
    _draw_line(page, x, y1, x, y2, gray=gray, width=width)


def _draw_rect(
    page,
    x,
    y,
    width,
    height,
    fill_gray=None,
    stroke_gray=PDF_COLOR_DARK,
    stroke_width=PDF_LINE_NORMAL,
):
    commands = []

    if fill_gray is not None:
        commands.append(f"{fill_gray} g {x} {y} {width} {height} re f")

    if stroke_gray is not None:
        commands.append(
            f"{stroke_gray} G {stroke_width} w {x} {y} {width} {height} re S"
        )

    page["commands"].extend(commands)


def _truncate_pdf_text(value, width):
    text = _format_cell(value)
    max_chars = max(8, int((width - 8) / 4.45))

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
        (
            f"2 0 obj << /Type /Pages /Kids [{' '.join(kids_refs)}] "
            f"/Count {len(pages)} >> endobj\n"
        ).encode("latin-1")
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
        content_stream = "\n".join(page["commands"]).encode(
            "latin-1",
            errors="replace",
        )
        objects.append(
            f"{content_object_id} 0 obj << /Length {len(content_stream)} >> stream\n".encode(
                "latin-1"
            )
            + content_stream
            + b"\nendstream endobj\n"
        )

    objects.append(
        (
            f"{font_regular_id} 0 obj << /Type /Font /Subtype /Type1 "
            f"/BaseFont /Helvetica >> endobj\n"
        ).encode("latin-1")
    )
    objects.append(
        (
            f"{font_bold_id} 0 obj << /Type /Font /Subtype /Type1 "
            f"/BaseFont /Helvetica-Bold >> endobj\n"
        ).encode("latin-1")
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
