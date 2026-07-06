from __future__ import annotations

import logging

import httpx
from django.conf import settings
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.permissions import IsAdmin, IsAdminOrReadOnly

from .models import MonedaModel, ProductoModel, ProductoPrecioModel
from .serializers import (
    MonedaSerializer,
    ProductoCreateSerializer,
    ProductoPrecioSerializer,
    ProductoSerializer,
)

logger = logging.getLogger(__name__)


def _index_product_embedding(producto: ProductoModel) -> None:
    """
    Fire-and-forget: send product to AI agent for embedding indexing.
    Never raises - product creation/update must not fail if agent is down.
    """
    try:
        url = f"{settings.AI_AGENT_SERVICE_URL}/api/v1/agent/embeddings/upsert/"
        with httpx.Client(timeout=10.0) as client:
            client.post(url, json={
                "producto_id": str(producto.id),
                "nombre": producto.nombre,
                "caracteristicas": producto.caracteristicas or "",
            })
    except Exception as exc:
        logger.warning("Embedding indexing failed for producto %s: %s", producto.id, exc)


class ProductoListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):  # type: ignore[override]
        qs = ProductoModel.objects.select_related("empresa").prefetch_related("precios__moneda")
        empresa_nit = self.request.query_params.get("empresa")
        if empresa_nit:
            qs = qs.filter(empresa_id=empresa_nit)
        if not (self.request.user.is_authenticated and self.request.user.rol == "admin"):
            qs = qs.filter(activo=True)
        return qs

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "POST":
            return ProductoCreateSerializer
        return ProductoSerializer

    def perform_create(self, serializer: ProductoCreateSerializer) -> None:  # type: ignore[override]
        from apps.inventory.models import InventarioModel

        try:
            cantidad_inicial = max(0, int(self.request.data.get("cantidad_inicial", 1) or 1))
        except (ValueError, TypeError):
            cantidad_inicial = 1

        producto = serializer.save()
        InventarioModel.objects.get_or_create(
            producto=producto,
            defaults={"cantidad": cantidad_inicial, "created_by": self.request.user},
        )
        _index_product_embedding(producto)


class ProductoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductoModel.objects.select_related("empresa").prefetch_related("precios__moneda")
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "id"

    def perform_update(self, serializer: ProductoSerializer) -> None:  # type: ignore[override]
        producto = serializer.save()
        _index_product_embedding(producto)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=["activo", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductoPrecioView(generics.CreateAPIView):
    serializer_class = ProductoPrecioSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer: ProductoPrecioSerializer) -> None:  # type: ignore[override]
        producto_id = self.kwargs["producto_id"]
        producto = generics.get_object_or_404(ProductoModel, id=producto_id)
        serializer.save(producto=producto)
        _index_product_embedding(producto)


class MonedaListView(generics.ListAPIView):
    queryset = MonedaModel.objects.filter(activo=True)
    serializer_class = MonedaSerializer
    permission_classes = [IsAdminOrReadOnly]
