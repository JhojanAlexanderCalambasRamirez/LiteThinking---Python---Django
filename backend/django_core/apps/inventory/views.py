import logging

import httpx
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.permissions import IsAdmin

from .models import InventarioModel
from .serializers import InventarioCreateSerializer, InventarioSerializer

logger = logging.getLogger(__name__)


class InventarioListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]

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
def export_and_email_inventory(request: Request) -> Response:
    """
    Delegates PDF generation + email sending to the FastAPI inventory microservice.
    Request body: { "empresa_nit": "...", "recipient_email": "..." }
    """
    empresa_nit = request.data.get("empresa_nit")
    recipient_email = request.data.get("recipient_email")

    if not empresa_nit or not recipient_email:
        return Response(
            {"error": "empresa_nit and recipient_email are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    inventory_items = (
        InventarioModel.objects.filter(producto__empresa_id=empresa_nit)
        .select_related("producto__empresa")
        .prefetch_related("producto__precios__moneda")
    )

    payload = {
        "empresa_nit": empresa_nit,
        "recipient_email": recipient_email,
        "items": [
            {
                "producto_codigo": item.producto.codigo,
                "producto_nombre": item.producto.nombre,
                "cantidad": item.cantidad,
                "precios": [
                    {"moneda": p.moneda_id, "precio": str(p.precio)}
                    for p in item.producto.precios.all()
                ],
            }
            for item in inventory_items
        ],
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{settings.INVENTORY_SERVICE_URL}/api/v1/inventory/export-email/",
                json=payload,
            )
            response.raise_for_status()
            return Response(response.json(), status=status.HTTP_200_OK)
    except httpx.HTTPError as exc:
        logger.error("Inventory service error: %s", exc)
        return Response(
            {"error": "Failed to reach inventory service. Try again later."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
