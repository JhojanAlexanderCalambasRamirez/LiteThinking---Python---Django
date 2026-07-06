import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.companies.models import EmpresaModel
from apps.users.models import UserModel

EMPRESAS_URL = "/api/v1/empresas/"


def empresa_url(nit: str) -> str:
    return f"{EMPRESAS_URL}{nit}/"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_user(db) -> UserModel:
    return UserModel.objects.create_user(
        email="admin@test.com", password="Admin1234!", rol="admin"
    )


@pytest.fixture
def externo_user(db) -> UserModel:
    return UserModel.objects.create_user(
        email="externo@test.com", password="Externo1234!", rol="externo"
    )


@pytest.fixture
def admin_client(client, admin_user) -> APIClient:
    res = client.post("/api/v1/auth/login/", {"email": "admin@test.com", "password": "Admin1234!"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return client


@pytest.fixture
def externo_client(client, externo_user) -> APIClient:
    res = client.post("/api/v1/auth/login/", {"email": "externo@test.com", "password": "Externo1234!"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return client


@pytest.fixture
def empresa_data() -> dict:
    return {
        "nit": "900123456-7",
        "nombre": "Test S.A.S.",
        "direccion": "Cra 7 # 32-16, Bogotá",
        "telefono": "+57 601 234 5678",
    }


@pytest.fixture
def empresa(db, empresa_data) -> EmpresaModel:
    return EmpresaModel.objects.create(**empresa_data)


class TestEmpresaList:
    def test_admin_can_list(self, admin_client, empresa) -> None:
        res = admin_client.get(EMPRESAS_URL)
        assert res.status_code == status.HTTP_200_OK

    def test_externo_can_list(self, externo_client, empresa) -> None:
        res = externo_client.get(EMPRESAS_URL)
        assert res.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_list(self, client, empresa) -> None:
        res = client.get(EMPRESAS_URL)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_empresa(self, admin_client, empresa) -> None:
        res = admin_client.get(EMPRESAS_URL)
        nits = [e["nit"] for e in (res.data.get("results") or res.data)]
        assert empresa.nit in nits

    def test_list_includes_direccion(self, admin_client, empresa) -> None:
        res = admin_client.get(EMPRESAS_URL)
        results = res.data.get("results") or res.data
        first = next(e for e in results if e["nit"] == empresa.nit)
        assert "direccion" in first


class TestEmpresaCreate:
    def test_admin_can_create(self, admin_client, empresa_data, db) -> None:
        res = admin_client.post(EMPRESAS_URL, empresa_data)
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["nit"] == empresa_data["nit"]

    def test_externo_cannot_create(self, externo_client, empresa_data, db) -> None:
        res = externo_client.post(EMPRESAS_URL, empresa_data)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create(self, client, empresa_data, db) -> None:
        res = client.post(EMPRESAS_URL, empresa_data)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_nit_returns_400(self, admin_client, empresa_data, db) -> None:
        empresa_data["nit"] = "abc-invalid"
        res = admin_client.post(EMPRESAS_URL, empresa_data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_nit_too_short_returns_400(self, admin_client, empresa_data, db) -> None:
        empresa_data["nit"] = "12345"
        res = admin_client.post(EMPRESAS_URL, empresa_data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_nit_returns_400(self, admin_client, empresa_data, empresa) -> None:
        res = admin_client.post(EMPRESAS_URL, empresa_data)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_created_empresa_is_active(self, admin_client, empresa_data, db) -> None:
        admin_client.post(EMPRESAS_URL, empresa_data)
        obj = EmpresaModel.objects.get(nit=empresa_data["nit"])
        assert obj.activo is True


class TestEmpresaDetail:
    def test_admin_can_retrieve(self, admin_client, empresa) -> None:
        res = admin_client.get(empresa_url(empresa.nit))
        assert res.status_code == status.HTTP_200_OK
        assert res.data["nombre"] == empresa.nombre

    def test_externo_can_retrieve(self, externo_client, empresa) -> None:
        res = externo_client.get(empresa_url(empresa.nit))
        assert res.status_code == status.HTTP_200_OK

    def test_nonexistent_returns_404(self, admin_client, db) -> None:
        res = admin_client.get(empresa_url("999999"))
        assert res.status_code == status.HTTP_404_NOT_FOUND


class TestEmpresaUpdate:
    def test_admin_can_update_nombre(self, admin_client, empresa) -> None:
        res = admin_client.patch(empresa_url(empresa.nit), {"nombre": "Nuevo Nombre S.A."})
        assert res.status_code == status.HTTP_200_OK
        empresa.refresh_from_db()
        assert empresa.nombre == "Nuevo Nombre S.A."

    def test_externo_cannot_update(self, externo_client, empresa) -> None:
        res = externo_client.patch(empresa_url(empresa.nit), {"nombre": "Hack"})
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_update_nit_without_products_succeeds(self, admin_client, empresa) -> None:
        res = admin_client.patch(empresa_url(empresa.nit), {"nit": "900000001-0"})
        assert res.status_code == status.HTTP_200_OK
        assert not EmpresaModel.objects.filter(nit=empresa.nit).exists()
        assert EmpresaModel.objects.filter(nit="900000001-0").exists()

    def test_update_invalid_nit_returns_400(self, admin_client, empresa) -> None:
        res = admin_client.patch(empresa_url(empresa.nit), {"nit": "abc"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


class TestEmpresaDelete:
    def test_admin_delete_soft_deactivates(self, admin_client, empresa) -> None:
        res = admin_client.delete(empresa_url(empresa.nit))
        assert res.status_code == status.HTTP_204_NO_CONTENT
        empresa.refresh_from_db()
        assert empresa.activo is False

    def test_externo_cannot_delete(self, externo_client, empresa) -> None:
        res = externo_client.delete(empresa_url(empresa.nit))
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_deactivated_empresa_hidden_from_externo(self, externo_client, empresa) -> None:
        empresa.activo = False
        empresa.save()
        res = externo_client.get(EMPRESAS_URL)
        results = res.data.get("results") if isinstance(res.data, dict) else res.data
        nits = [e["nit"] for e in (results or [])]
        assert empresa.nit not in nits
