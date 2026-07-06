import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import UserModel


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_user(db) -> UserModel:
    return UserModel.objects.create_user(
        email="admin@test.com",
        password="Admin1234!",
        rol="admin",
    )


@pytest.fixture
def externo_user(db) -> UserModel:
    return UserModel.objects.create_user(
        email="externo@test.com",
        password="Externo1234!",
        rol="externo",
    )


LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"


class TestLogin:
    def test_admin_login_returns_tokens(self, client, admin_user) -> None:
        res = client.post(LOGIN_URL, {"email": "admin@test.com", "password": "Admin1234!"})
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data
        assert "refresh" in res.data

    def test_externo_login_returns_tokens(self, client, externo_user) -> None:
        res = client.post(LOGIN_URL, {"email": "externo@test.com", "password": "Externo1234!"})
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data

    def test_login_response_includes_role(self, client, admin_user) -> None:
        res = client.post(LOGIN_URL, {"email": "admin@test.com", "password": "Admin1234!"})
        assert res.data.get("rol") == "admin"

    def test_wrong_password_returns_401(self, client, admin_user) -> None:
        res = client.post(LOGIN_URL, {"email": "admin@test.com", "password": "wrongpassword"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unknown_email_returns_401(self, client, db) -> None:
        res = client.post(LOGIN_URL, {"email": "nobody@test.com", "password": "any"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_credentials_returns_400(self, client, db) -> None:
        res = client.post(LOGIN_URL, {})
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_password_returns_400(self, client, admin_user) -> None:
        res = client.post(LOGIN_URL, {"email": "admin@test.com"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


class TestTokenRefresh:
    def test_valid_refresh_token_returns_new_access(self, client, admin_user) -> None:
        login_res = client.post(LOGIN_URL, {"email": "admin@test.com", "password": "Admin1234!"})
        refresh = login_res.data["refresh"]
        res = client.post(REFRESH_URL, {"refresh": refresh})
        assert res.status_code == status.HTTP_200_OK
        assert "access" in res.data

    def test_invalid_refresh_token_returns_401(self, client, db) -> None:
        res = client.post(REFRESH_URL, {"refresh": "not.a.valid.token"})
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


REGISTER_URL = "/api/v1/users/register/"


class TestRegister:
    def test_register_creates_externo_user(self, client, db) -> None:
        res = client.post(REGISTER_URL, {
            "email": "nuevo@test.com",
            "password": "Nuevo1234!",
            "nombre": "Juan",
        })
        assert res.status_code == status.HTTP_201_CREATED
        user = UserModel.objects.get(email="nuevo@test.com")
        assert user.rol == "externo"

    def test_register_duplicate_email_returns_400(self, client, externo_user) -> None:
        res = client.post(REGISTER_URL, {
            "email": "externo@test.com",
            "password": "Other1234!",
            "nombre": "Otro",
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_self_register_as_admin(self, client, db) -> None:
        res = client.post(REGISTER_URL, {
            "email": "hack@test.com",
            "password": "Hack1234!",
            "nombre": "Hack",
            "rol": "admin",
        })
        assert res.status_code == status.HTTP_201_CREATED
        user = UserModel.objects.get(email="hack@test.com")
        assert user.rol == "externo"
