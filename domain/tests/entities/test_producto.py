import pytest
from decimal import Decimal

from litethinking_domain.entities import Producto
from litethinking_domain.exceptions import InvalidMoneyError
from litethinking_domain.value_objects import NIT, Money


def make_producto() -> Producto:
    return Producto(
        codigo="PROD-001",
        nombre="Laptop Dell XPS",
        empresa_nit=NIT("900123456-7"),
        caracteristicas="Intel i7, 16GB RAM, 512GB SSD",
    )


class TestProducto:
    def test_create_producto(self) -> None:
        p = make_producto()
        assert p.activo is True
        assert p.precios == {}

    def test_agregar_precio(self) -> None:
        p = make_producto()
        p.agregar_precio(Money.of(4_500_000, "COP"))
        assert p.precio_en("COP") is not None
        assert p.precio_en("COP").amount == Decimal("4500000")

    def test_precio_multi_moneda(self) -> None:
        p = make_producto()
        p.agregar_precio(Money.of(1_200, "USD"))
        p.agregar_precio(Money.of(4_500_000, "COP"))
        assert len(p.precios) == 2

    def test_actualizar_precio_overwrites(self) -> None:
        p = make_producto()
        p.agregar_precio(Money.of(1_200, "USD"))
        p.actualizar_precio(Money.of(1_350, "USD"))
        assert p.precio_en("USD").amount == Decimal("1350")

    def test_eliminar_precio(self) -> None:
        p = make_producto()
        p.agregar_precio(Money.of(1_200, "USD"))
        p.eliminar_precio("USD")
        assert p.precio_en("USD") is None

    def test_precio_negativo_raises(self) -> None:
        with pytest.raises(InvalidMoneyError):
            Money.of(-100, "USD")

    def test_desactivar_producto(self) -> None:
        p = make_producto()
        p.desactivar()
        assert p.activo is False
