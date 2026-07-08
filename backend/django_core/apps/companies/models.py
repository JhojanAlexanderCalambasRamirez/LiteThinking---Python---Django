from __future__ import annotations

from django.core.validators import RegexValidator
from django.db import models

from litethinking_domain.entities import Empresa
from litethinking_domain.value_objects import NIT

_NIT_REGEX = r"^\d{6,10}(-\d)?$"
_TELEFONO_REGEX = r"^\+?[\d\s\-\(\)]{7,20}$"


class EmpresaModel(models.Model):
    nit = models.CharField(
        max_length=20,
        primary_key=True,
        validators=[RegexValidator(
            regex=_NIT_REGEX,
            message="NIT inválido. Formato: 6-10 dígitos, opcionalmente '-' + dígito verificador. Ej: 900123456-7",
        )],
    )
    nombre = models.CharField(max_length=255)
    direccion = models.TextField()
    telefono = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=_TELEFONO_REGEX,
            message="Teléfono inválido. Formato: +57 601 234 5678",
        )],
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empresa"
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nit__regex=_NIT_REGEX),
                name="chk_empresa_nit_format",
                violation_error_message="NIT inválido. Formato: 6-10 dígitos, opcionalmente '-' + dígito verificador.",
            ),
            models.CheckConstraint(
                condition=models.Q(telefono__regex=_TELEFONO_REGEX),
                name="chk_empresa_telefono_format",
                violation_error_message="Teléfono inválido.",
            ),
        ]

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
