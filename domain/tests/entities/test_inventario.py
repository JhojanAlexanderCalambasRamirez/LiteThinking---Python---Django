import pytest
from uuid import uuid4

from litethinking_domain.entities import Inventario
from litethinking_domain.exceptions import InsufficientStockError


def make_inventario(cantidad: int = 10) -> Inventario:
    return Inventario(
        producto_id=uuid4(),
        cantidad=cantidad,
        created_by=uuid4(),
    )


class TestInventario:
    def test_create_inventario(self) -> None:
        inv = make_inventario(5)
        assert inv.cantidad == 5

    def test_incrementar(self) -> None:
        inv = make_inventario(10)
        inv.incrementar(5)
        assert inv.cantidad == 15

    def test_decrementar(self) -> None:
        inv = make_inventario(10)
        inv.decrementar(3)
        assert inv.cantidad == 7

    def test_decrementar_insufficient_raises(self) -> None:
        inv = make_inventario(5)
        with pytest.raises(InsufficientStockError):
            inv.decrementar(10)

    def test_cantidad_negativa_en_creacion_raises(self) -> None:
        with pytest.raises(ValueError):
            make_inventario(-1)

    def test_ajustar_cantidad(self) -> None:
        inv = make_inventario(10)
        inv.ajustar_cantidad(50)
        assert inv.cantidad == 50

    def test_ajustar_cantidad_negativa_raises(self) -> None:
        inv = make_inventario(10)
        with pytest.raises(ValueError):
            inv.ajustar_cantidad(-5)
