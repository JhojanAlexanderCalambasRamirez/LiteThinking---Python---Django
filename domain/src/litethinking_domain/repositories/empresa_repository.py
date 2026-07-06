from __future__ import annotations

from abc import ABC, abstractmethod

from litethinking_domain.entities import Empresa
from litethinking_domain.value_objects import NIT


class EmpresaRepository(ABC):
    """
    Port (abstract interface) for Empresa persistence.
    Implementations live in infrastructure (Django ORM, SQLAlchemy, etc.).
    Domain layer has zero knowledge of how data is stored.
    """

    @abstractmethod
    def find_by_nit(self, nit: NIT) -> Empresa | None: ...

    @abstractmethod
    def find_all(self, include_inactive: bool = False) -> list[Empresa]: ...

    @abstractmethod
    def exists_by_nit(self, nit: NIT) -> bool: ...

    @abstractmethod
    def save(self, empresa: Empresa) -> Empresa: ...

    @abstractmethod
    def delete(self, nit: NIT) -> None:
        """Soft delete - sets activo=False."""
