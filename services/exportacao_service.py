from datetime import datetime
from io import BytesIO

from services.relatorios_service import build_relatorio_ponto


EXPORT_COLUMNS = (
    ("data", "Data"),
    ("hora", "Hora"),
    ("tipo_label", "Tipo"),
    ("funcionario", "Funcionario"),
    ("latitude", "Latitude"),
    ("longitude", "Longitude"),
    ("foto_url", "Foto URL"),
)


def exportar_excel(filters):
    relatorio = build_relatorio_ponto(filters)
    rows = _serialize_rows(relatorio["registros"])

    content = _build_excel_xml(rows).encode("utf-8")
    filename = _build_filename("relatorio_ponto", "xls")
    mimetype = "application/vnd.ms-excel"

    return content, filename, mimetype


def exportar_pdf(filters):
    relatorio = build_relatorio_ponto(filters)
    rows = _serialize_rows(relatorio["registros"])

    pdf_content = _build_simple_pdf(rows)
    filename = _build_filename("relatorio_ponto", "pdf")
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


def _build_simple_pdf(rows):
    pdf_buffer = BytesIO()
    lines = ["Relatorio de Ponto", ""]
    header = " | ".join(column_label for _, column_label in EXPORT_COLUMNS)
    lines.append(header)
    lines.append("-" * len(header))

    for row in rows:
        lines.append(" | ".join(_sanitize_pdf_text(cell) for cell in row))

    if len(rows) == 0:
        lines.append("Nenhum registro encontrado.")

    text_stream = "\n".join(lines)
    pdf_bytes = _render_minimal_pdf(text_stream)
    pdf_buffer.write(pdf_bytes)
    return pdf_buffer.getvalue()


def _build_excel_xml(rows):
    header_cells = "".join(
        f"<Cell><Data ss:Type=\"String\">{_escape_xml(column_label)}</Data></Cell>"
        for _, column_label in EXPORT_COLUMNS
    )

    row_xml = [f"<Row>{header_cells}</Row>"]

    for row in rows:
        cells = "".join(
            f"<Cell><Data ss:Type=\"String\">{_escape_xml(cell)}</Data></Cell>"
            for cell in row
        )
        row_xml.append(f"<Row>{cells}</Row>")

    if not rows:
        row_xml.append(
            "<Row><Cell><Data ss:Type=\"String\">Nenhum registro encontrado.</Data></Cell></Row>"
        )

    return (
        "<?xml version=\"1.0\"?>"
        "<?mso-application progid=\"Excel.Sheet\"?>"
        "<Workbook "
        "xmlns=\"urn:schemas-microsoft-com:office:spreadsheet\" "
        "xmlns:o=\"urn:schemas-microsoft-com:office:office\" "
        "xmlns:x=\"urn:schemas-microsoft-com:office:excel\" "
        "xmlns:ss=\"urn:schemas-microsoft-com:office:spreadsheet\">"
        "<Worksheet ss:Name=\"Relatorio\">"
        "<Table>"
        f"{''.join(row_xml)}"
        "</Table>"
        "</Worksheet>"
        "</Workbook>"
    )


def _escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _sanitize_pdf_text(value):
    sanitized = str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    sanitized = sanitized.replace("\r", " ").replace("\n", " ")
    return sanitized


def _render_minimal_pdf(text):
    content_lines = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]

    for index, line in enumerate(text.split("\n")):
        if index == 0:
            content_lines.append(f"({line}) Tj")
        else:
            content_lines.append("T*")
            content_lines.append(f"({line}) Tj")

    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    )
    objects.append(
        f"5 0 obj << /Length {len(content_stream)} >> stream\n".encode("latin-1")
        + content_stream
        + b"\nendstream endobj\n"
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
