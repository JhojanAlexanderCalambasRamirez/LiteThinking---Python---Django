from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from litethinking_domain.entities import Usuario
from litethinking_domain.value_objects import EmailAddress


class UsuarioRepository(ABC):
    """Port for Usuario persistence."""

    @abstractmethod
    def find_by_id(self, usuario_id: UUID) -> Usuario | None: ...

    @abstractmethod
    def find_by_email(self, email: EmailAddress) -> Usuario | None: ...

    @abstractmethod
    def exists_by_email(self, email: EmailAddress) -> bool: ...

    @abstractmethod
    def save(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def delete(self, usuario_id: UUID) -> None:
        """Soft delete - sets activo=False."""
