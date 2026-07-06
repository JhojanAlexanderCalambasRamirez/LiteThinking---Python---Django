from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, field_validator

from services.email_service import send_inventory_email
from services.pdf_service import generate_inventory_pdf

router = APIRouter(tags=["inventory"])


class PrecioItem(BaseModel):
    moneda: str
    precio: str


class InventarioItem(BaseModel):
    producto_codigo: str
    producto_nombre: str
    caracteristicas: str | None = None
    cantidad: int
    precios: list[PrecioItem] = []


class ExportEmailRequest(BaseModel):
    empresa_nit: str
    empresa_nombre: str | None = None
    recipient_email: EmailStr
    items: list[InventarioItem]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("items list cannot be empty.")
        return v


@router.post("/inventory/export-email/")
async def export_and_email(payload: ExportEmailRequest) -> dict[str, Any]:
    """
    Generate inventory PDF and send it to the given email.
    Called internally by the Django backend.
    """
    empresa_nombre = payload.empresa_nombre or payload.empresa_nit
    items_dicts = [item.model_dump() for item in payload.items]

    pdf_bytes = generate_inventory_pdf(
        empresa_nit=payload.empresa_nit,
        empresa_nombre=empresa_nombre,
        items=items_dicts,
    )

    filename = f"inventario_{payload.empresa_nit}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    sent = send_inventory_email(
        recipient_email=payload.recipient_email,
        empresa_nombre=empresa_nombre,
        pdf_bytes=pdf_bytes,
        filename=filename,
    )

    if not sent:
        raise HTTPException(status_code=502, detail="Failed to send email. Check SMTP/SendGrid config.")

    return {
        "message": f"Inventory PDF sent to {payload.recipient_email}.",
        "filename": filename,
        "items_count": len(payload.items),
    }


@router.post("/inventory/export-pdf/")
async def export_pdf(payload: ExportEmailRequest) -> StreamingResponse:
    """Return the PDF directly as a download (no email)."""
    import io

    empresa_nombre = payload.empresa_nombre or payload.empresa_nit
    pdf_bytes = generate_inventory_pdf(
        empresa_nit=payload.empresa_nit,
        empresa_nombre=empresa_nombre,
        items=[item.model_dump() for item in payload.items],
    )

    filename = f"inventario_{payload.empresa_nit}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
