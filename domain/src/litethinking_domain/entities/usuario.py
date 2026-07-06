from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from litethinking_domain.value_objects import EmailAddress, PasswordHash


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    ADMIN = "admin"
    EXTERNO = "externo"


@dataclass
class Usuario:
    """
    Core business entity representing an application user.
    Stores only the password hash - never plaintext.
    """

    email: EmailAddress
    password_hash: PasswordHash
    rol: UserRole
    nombre: str | None = None
    apellido: str | None = None
    activo: bool = True
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def es_admin(self) -> bool:
        return self.rol == UserRole.ADMIN

    def es_externo(self) -> bool:
        return self.rol == UserRole.EXTERNO

    def puede_modificar_empresa(self) -> bool:
        return self.es_admin() and self.activo

    def puede_gestionar_productos(self) -> bool:
        return self.es_admin() and self.activo

    def puede_gestionar_inventario(self) -> bool:
        return self.es_admin() and self.activo

    def cambiar_password(self, new_hash: PasswordHash) -> None:
        self.password_hash = new_hash
        self.updated_at = _utcnow()

    def desactivar(self) -> None:
        self.activo = False
        self.updated_at = _utcnow()

    def activar(self) -> None:
        self.activo = True
        self.updated_at = _utcnow()

    def nombre_completo(self) -> str:
        parts = filter(None, [self.nombre, self.apellido])
        return " ".join(parts) or str(self.email)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Usuario):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"Usuario(id={self.id!r}, email={self.email!r}, "
            f"rol={self.rol.value!r}, activo={self.activo})"
        )
