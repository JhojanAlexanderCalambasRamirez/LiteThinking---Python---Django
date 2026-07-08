from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from litethinking_domain.exceptions import ProductoAlreadyExistsError
from litethinking_domain.value_objects import NIT, Money


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Producto:
    codigo: str
    nombre: str
    empresa_nit: NIT
    caracteristicas: str | None = None
    activo: bool = True
    id: UUID = field(default_factory=uuid4)
    precios: dict[str, Money] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ValueError("Producto codigo cannot be empty.")
        if not self.nombre or not self.nombre.strip():
            raise ValueError("Producto nombre cannot be empty.")

    def agregar_precio(self, money: Money) -> None:
        self.precios[money.currency] = money
        self.updated_at = _utcnow()

    def actualizar_precio(self, money: Money) -> None:
        self.precios[money.currency] = money
        self.updated_at = _utcnow()

    def eliminar_precio(self, currency: str) -> None:
        self.precios.pop(currency.upper(), None)
        self.updated_at = _utcnow()

    def precio_en(self, currency: str) -> Money | None:
        return self.precios.get(currency.upper())

    def actualizar(
        self,
        nombre: str,
        caracteristicas: str | None = None,
    ) -> None:
        if not nombre or not nombre.strip():
            raise ValueError("Producto nombre cannot be empty.")
        self.nombre = nombre.strip()
        self.caracteristicas = caracteristicas
        self.updated_at = _utcnow()

    def desactivar(self) -> None:
        self.activo = False
        self.updated_at = _utcnow()

    def activar(self) -> None:
        self.activo = True
        self.updated_at = _utcnow()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Producto):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"Producto(id={self.id!r}, codigo={self.codigo!r}, "
            f"nombre={self.nombre!r}, empresa_nit={self.empresa_nit!r})"
        )
