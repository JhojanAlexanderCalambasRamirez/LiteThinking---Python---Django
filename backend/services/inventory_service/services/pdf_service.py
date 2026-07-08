from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_inventory_pdf(
    empresa_nit: str,
    empresa_nombre: str,
    items: list[dict],
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("REPORTE DE INVENTARIO", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"<b>Empresa:</b> {empresa_nombre}", styles["Normal"]))
    story.append(Paragraph(f"<b>NIT:</b> {empresa_nit}", styles["Normal"]))
    story.append(
        Paragraph(
            f"<b>Generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * inch))

    # Table header
    headers = ["Código", "Nombre", "Características", "Cantidad", "Precios"]
    table_data = [headers]

    for item in items:
        precios_str = "\n".join(
            f"{p['moneda']}: {p['precio']}" for p in item.get("precios", [])
        )
        table_data.append([
            item.get("producto_codigo", ""),
            item.get("producto_nombre", ""),
            item.get("caracteristicas", "-"),
            str(item.get("cantidad", 0)),
            precios_str or "-",
        ])

    table = Table(
        table_data,
        colWidths=[1.0 * inch, 2.0 * inch, 2.0 * inch, 0.8 * inch, 1.5 * inch],
    )
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("WORDWRAP", (0, 0), (-1, -1), True),
        ])
    )

    story.append(table)
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            f"<i>Total de registros: {len(items)}</i>",
            styles["Normal"],
        )
    )

    doc.build(story)
    return buffer.getvalue()
