import pytest

from litethinking_domain.entities import Empresa
from litethinking_domain.exceptions import InvalidNITError
from litethinking_domain.value_objects import NIT


def make_empresa(nit: str = "900123456-7") -> Empresa:
    return Empresa(
        nit=NIT(nit),
        nombre="Test S.A.S.",
        direccion="Cra 7 # 32-16, Bogotá",
        telefono="+57 601 234 5678",
    )


class TestNIT:
    def test_valid_nit_with_check_digit(self) -> None:
        nit = NIT("900123456-7")
        assert str(nit) == "900123456-7"

    def test_valid_nit_without_check_digit(self) -> None:
        nit = NIT("900123456")
        assert str(nit) == "900123456"

    def test_invalid_nit_raises(self) -> None:
        with pytest.raises(InvalidNITError):
            NIT("abc-xyz")

    def test_nit_equality(self) -> None:
        assert NIT("900123456-7") == NIT("900123456-7")

    def test_nit_immutable(self) -> None:
        nit = NIT("900123456-7")
        with pytest.raises(Exception):
            nit.valor = "other"  # type: ignore[misc]


class TestEmpresa:
    def test_create_empresa(self) -> None:
        empresa = make_empresa()
        assert empresa.activo is True
        assert str(empresa.nit) == "900123456-7"

    def test_actualizar_empresa(self) -> None:
        empresa = make_empresa()
        empresa.actualizar("Nueva Razón S.A.", "Nueva Dir 123", "3001234567")
        assert empresa.nombre == "Nueva Razón S.A."

    def test_desactivar_empresa(self) -> None:
        empresa = make_empresa()
        empresa.desactivar()
        assert empresa.activo is False

    def test_activar_empresa(self) -> None:
        empresa = make_empresa()
        empresa.desactivar()
        empresa.activar()
        assert empresa.activo is True

    def test_empresa_empty_nombre_raises(self) -> None:
        with pytest.raises(ValueError):
            make_empresa().actualizar("", "dir", "tel")

    def test_empresa_equality_by_nit(self) -> None:
        e1 = make_empresa("900123456-7")
        e2 = make_empresa("900123456-7")
        assert e1 == e2
