from __future__ import annotations

import logging

import httpx
from django.conf import settings
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.permissions import IsAdmin, IsAdminOrReadOnly

from .models import InventarioModel
from .serializers import InventarioCreateSerializer, InventarioSerializer

logger = logging.getLogger(__name__)


def _build_inventory_payload(empresa_nit: str) -> dict:
    """Fetch inventory items for a company and build the microservice payload."""
    items_qs = (
        InventarioModel.objects.filter(producto__empresa_id=empresa_nit, cantidad__gt=0)
        .select_related("producto__empresa")
        .prefetch_related("producto__precios__moneda")
    )
    empresa_nombre = (
        items_qs.first().producto.empresa.nombre if items_qs.exists() else empresa_nit
    )
    return {
        "empresa_nit": empresa_nit,
        "empresa_nombre": empresa_nombre,
        "items": [
            {
                "producto_codigo": item.producto.codigo,
                "producto_nombre": item.producto.nombre,
                "caracteristicas": item.producto.caracteristicas or "",
                "cantidad": item.cantidad,
                "precios": [
                    {"moneda": p.moneda_id, "precio": str(p.precio)}
                    for p in item.producto.precios.all()
                ],
            }
            for item in items_qs
        ],
    }


class InventarioListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):  # type: ignore[override]
        qs = InventarioModel.objects.select_related(
            "producto__empresa", "created_by"
        ).prefetch_related("producto__precios__moneda")
        empresa_nit = self.request.query_params.get("empresa")
        if empresa_nit:
            qs = qs.filter(producto__empresa_id=empresa_nit)
        return qs

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return InventarioCreateSerializer
        return InventarioSerializer

    def perform_create(self, serializer: InventarioCreateSerializer) -> None:  # type: ignore[override]
        serializer.save(created_by=self.request.user)


class InventarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventarioModel.objects.select_related("producto__empresa", "created_by")
    permission_classes = [IsAdmin]
    lookup_field = "id"

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method in ("PUT", "PATCH"):
            return InventarioCreateSerializer
        return InventarioSerializer


@api_view(["POST"])
@permission_classes([IsAdmin])
def export_pdf_inventory(request: Request) -> HttpResponse:
    """
    Generate and stream inventory PDF directly to the browser.
    Body: { "empresa_nit": "..." }
    """
    empresa_nit = request.data.get("empresa_nit")
    if not empresa_nit:
        return Response({"error": "empresa_nit is required."}, status=status.HTTP_400_BAD_REQUEST)

    payload = _build_inventory_payload(empresa_nit)

    if not payload["items"]:
        return Response(
            {"error": "No hay productos con stock disponible para exportar (cantidad > 0)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{settings.INVENTORY_SERVICE_URL}/api/v1/inventory/export-pdf/",
                json=payload,
            )
            response.raise_for_status()

        filename = f"inventario_{empresa_nit}.pdf"
        return HttpResponse(
            response.content,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except httpx.HTTPError as exc:
        logger.error("Inventory service error (PDF): %s", exc)
        return Response(
            {"error": "No se pudo generar el PDF. Intente de nuevo."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["POST"])
@permission_classes([IsAdmin])
def export_and_email_inventory(request: Request) -> Response:
    """
    Generate inventory PDF and send it by email.
    Body: { "empresa_nit": "...", "recipient_email": "..." }
    """
    empresa_nit = request.data.get("empresa_nit")
    recipient_email = request.data.get("recipient_email")

    if not empresa_nit or not recipient_email:
        return Response(
            {"error": "empresa_nit and recipient_email are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    payload = _build_inventory_payload(empresa_nit)
    payload["recipient_email"] = recipient_email

    if not payload["items"]:
        return Response(
            {"error": "No hay productos con stock disponible para exportar (cantidad > 0)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{settings.INVENTORY_SERVICE_URL}/api/v1/inventory/export-email/",
                json=payload,
            )
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
    except httpx.HTTPError as exc:
        logger.error("Inventory service error (email): %s", exc)
        return Response(
            {"error": "No se pudo enviar el email. Verifique la configuración SMTP."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
