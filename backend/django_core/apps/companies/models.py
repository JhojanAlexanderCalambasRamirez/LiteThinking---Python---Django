from __future__ import annotations

from django.db import models

from litethinking_domain.entities import Empresa
from litethinking_domain.value_objects import NIT


class EmpresaModel(models.Model):
    """
    Django ORM model for Empresa.
    PK is NIT (natural business key, VARCHAR).
    """

    nit = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=255)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empresa"
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nombre"]

    def to_domain(self) -> Empresa:
        return Empresa(
            nit=NIT(self.nit),
            nombre=self.nombre,
            direccion=self.direccion,
            telefono=self.telefono,
            activo=self.activo,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, empresa: Empresa) -> EmpresaModel:
        return cls(
            nit=str(empresa.nit),
            nombre=empresa.nombre,
            direccion=empresa.direccion,
            telefono=empresa.telefono,
            activo=empresa.activo,
        )

    def __str__(self) -> str:
        return f"{self.nombre} ({self.nit})"
