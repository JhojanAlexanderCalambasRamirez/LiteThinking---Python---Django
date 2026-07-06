from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from litethinking_domain.entities import Inventario
from litethinking_domain.value_objects import NIT


class InventarioRepository(ABC):
    """Port for Inventario persistence."""

    @abstractmethod
    def find_by_id(self, inventario_id: UUID) -> Inventario | None: ...

    @abstractmethod
    def find_by_producto_id(self, producto_id: UUID) -> Inventario | None: ...

    @abstractmethod
    def find_all_by_empresa(self, empresa_nit: NIT) -> list[Inventario]: ...

    @abstractmethod
    def save(self, inventario: Inventario) -> Inventario: ...

    @abstractmethod
    def delete(self, inventario_id: UUID) -> None: ...
