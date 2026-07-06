from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class InventarioModel(models.Model):
    """
    One inventory entry per product.
    Empresa is derived via producto → empresa_nit (no redundant FK).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.OneToOneField(
        "products.ProductoModel",
        on_delete=models.PROTECT,
        related_name="inventario",
    )
    cantidad = models.PositiveIntegerField(default=1)
    observaciones = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inventario_entries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventario"
        verbose_name = "Inventario"
        verbose_name_plural = "Inventario"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Inventario: {self.producto.nombre} - {self.cantidad} unidades"
