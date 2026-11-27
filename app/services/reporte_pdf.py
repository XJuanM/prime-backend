"""Generación del PDF de un reporte (sin dependencias de la base de datos)."""

from datetime import date, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_HEADER_BG = colors.HexColor("#1f2937")
_ZEBRA_BG = colors.HexColor("#f3f4f6")


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _table(data: list[list[str]], col_widths=None) -> Table:
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ZEBRA_BG]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_report_pdf(
    *,
    titulo: str,
    tipo_label: str,
    fecha_inicio: date,
    fecha_fin: date,
    descripcion: str | None,
    indicadores: dict[str, Any],
    columnas: list[str],
    filas: list[list[Any]],
    generado_por: str,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=titulo,
        author="Prime",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=20, spaceAfter=6)
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6
    )
    meta = ParagraphStyle(
        "Meta", parent=styles["Normal"], fontSize=9, textColor=colors.grey
    )
    body = styles["Normal"]

    story: list = [
        Paragraph(_escape(titulo), h1),
        Paragraph(
            f"Tipo: {_escape(tipo_label)} &nbsp;|&nbsp; "
            f"Periodo: {fecha_inicio:%d/%m/%Y} - {fecha_fin:%d/%m/%Y}",
            meta,
        ),
        Paragraph(
            f"Generado el {datetime.now():%d/%m/%Y %H:%M} por "
            f"{_escape(generado_por)}",
            meta,
        ),
    ]

    if descripcion:
        story += [Spacer(1, 8), Paragraph(_escape(descripcion), body)]

    story.append(Paragraph("Resumen", h2))
    if indicadores:
        story.append(
            _table(
                [["Indicador", "Valor"]]
                + [[k, _fmt(v)] for k, v in indicadores.items()],
                col_widths=[9 * cm, 8 * cm],
            )
        )
    else:
        story.append(Paragraph("Sin indicadores para este periodo.", body))

    story.append(Paragraph("Detalle", h2))
    if filas:
        ancho = 17 * cm / max(len(columnas), 1)
        story.append(
            _table(
                [columnas] + [[_fmt(c) for c in fila] for fila in filas],
                col_widths=[ancho] * len(columnas),
            )
        )
    else:
        story.append(
            Paragraph("No hay datos en el periodo seleccionado.", body)
        )

    doc.build(story)
    return buffer.getvalue()