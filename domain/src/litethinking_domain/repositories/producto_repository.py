from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from litethinking_domain.entities import Producto
from litethinking_domain.value_objects import NIT


class ProductoRepository(ABC):
    """Port for Producto persistence."""

    @abstractmethod
    def find_by_id(self, producto_id: UUID) -> Producto | None: ...

    @abstractmethod
    def find_by_codigo_and_empresa(self, codigo: str, empresa_nit: NIT) -> Producto | None: ...

    @abstractmethod
    def find_all_by_empresa(
        self, empresa_nit: NIT, include_inactive: bool = False
    ) -> list[Producto]: ...

    @abstractmethod
    def exists_by_codigo_and_empresa(self, codigo: str, empresa_nit: NIT) -> bool: ...

    @abstractmethod
    def save(self, producto: Producto) -> Producto: ...

    @abstractmethod
    def delete(self, producto_id: UUID) -> None:
        """Soft delete - sets activo=False."""
