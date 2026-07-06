from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from litethinking_domain.entities import Producto
from litethinking_domain.value_objects import NIT, Money


class MonedaModel(models.Model):
    codigo = models.CharField(max_length=3, primary_key=True)
    nombre = models.CharField(max_length=50)
    simbolo = models.CharField(max_length=5)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "moneda"
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class ProductoModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    caracteristicas = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(
        "companies.EmpresaModel",
        on_delete=models.PROTECT,
        related_name="productos",
        db_column="empresa_nit",
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = [("codigo", "empresa")]
        ordering = ["nombre"]

    def to_domain(self) -> Producto:
        producto = Producto(
            id=self.id,
            codigo=self.codigo,
            nombre=self.nombre,
            empresa_nit=NIT(self.empresa_id),
            caracteristicas=self.caracteristicas,
            activo=self.activo,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        for precio_model in self.precios.select_related("moneda").all():
            money = Money.of(precio_model.precio, precio_model.moneda_id)
            producto.precios[money.currency] = money
        return producto

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class ProductoPrecioModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producto = models.ForeignKey(
        ProductoModel,
        on_delete=models.CASCADE,
        related_name="precios",
    )
    moneda = models.ForeignKey(
        MonedaModel,
        on_delete=models.PROTECT,
        db_column="moneda_codigo",
    )
    precio = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "producto_precio"
        unique_together = [("producto", "moneda")]
        verbose_name = "Precio de Producto"
        verbose_name_plural = "Precios de Productos"

    def __str__(self) -> str:
        return f"{self.producto.codigo} - {self.precio} {self.moneda_id}"
