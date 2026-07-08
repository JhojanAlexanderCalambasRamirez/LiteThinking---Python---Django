from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from litethinking_domain.value_objects import NIT


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Empresa:
    nit: NIT
    nombre: str
    direccion: str
    telefono: str
    activo: bool = True
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValueError("Empresa nombre cannot be empty.")
        if not self.direccion or not self.direccion.strip():
            raise ValueError("Empresa direccion cannot be empty.")
        if not self.telefono or not self.telefono.strip():
            raise ValueError("Empresa telefono cannot be empty.")

    def actualizar(self, nombre: str, direccion: str, telefono: str) -> None:
        if not nombre or not nombre.strip():
            raise ValueError("Empresa nombre cannot be empty.")
        if not direccion or not direccion.strip():
            raise ValueError("Empresa direccion cannot be empty.")
        if not telefono or not telefono.strip():
            raise ValueError("Empresa telefono cannot be empty.")

        self.nombre = nombre.strip()
        self.direccion = direccion.strip()
        self.telefono = telefono.strip()
        self.updated_at = _utcnow()

    def desactivar(self) -> None:
        self.activo = False
        self.updated_at = _utcnow()

    def activar(self) -> None:
        self.activo = True
        self.updated_at = _utcnow()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Empresa):
            return NotImplemented
        return self.nit == other.nit

    def __hash__(self) -> int:
        return hash(self.nit)

    def __repr__(self) -> str:
        return f"Empresa(nit={self.nit!r}, nombre={self.nombre!r}, activo={self.activo})"
