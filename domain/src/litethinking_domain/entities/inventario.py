from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from litethinking_domain.exceptions import InsufficientStockError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Inventario:
    """
    Inventory entry tracking stock for a single product.
    Business rule: quantity cannot be negative.
    Empresa is resolved via producto_id → Producto → empresa_nit (avoid redundancy).
    """

    producto_id: UUID
    cantidad: int
    created_by: UUID
    observaciones: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self._validate_cantidad(self.cantidad)

    def _validate_cantidad(self, cantidad: int) -> None:
        if cantidad < 0:
            raise ValueError(
                f"Inventario cantidad cannot be negative. Got: {cantidad}"
            )

    def ajustar_cantidad(self, nueva_cantidad: int) -> None:
        self._validate_cantidad(nueva_cantidad)
        self.cantidad = nueva_cantidad
        self.updated_at = _utcnow()

    def incrementar(self, unidades: int) -> None:
        if unidades <= 0:
            raise ValueError(f"Units to add must be positive. Got: {unidades}")
        self.cantidad += unidades
        self.updated_at = _utcnow()

    def decrementar(self, unidades: int) -> None:
        if unidades <= 0:
            raise ValueError(f"Units to remove must be positive. Got: {unidades}")
        if unidades > self.cantidad:
            raise InsufficientStockError(
                producto_id=str(self.producto_id),
                requested=unidades,
                available=self.cantidad,
            )
        self.cantidad -= unidades
        self.updated_at = _utcnow()

    def actualizar_observaciones(self, observaciones: str | None) -> None:
        self.observaciones = observaciones
        self.updated_at = _utcnow()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Inventario):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"Inventario(id={self.id!r}, producto_id={self.producto_id!r}, "
            f"cantidad={self.cantidad})"
        )
