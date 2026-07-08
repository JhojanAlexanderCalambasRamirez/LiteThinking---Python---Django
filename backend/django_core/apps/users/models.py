from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from litethinking_domain.entities import Usuario, UserRole
from litethinking_domain.value_objects import EmailAddress, PasswordHash


class UserModelManager(BaseUserManager["UserModel"]):
    def create_user(
        self, email: str, password: str, rol: str = "externo", **extra_fields: object
    ) -> UserModel:
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, rol=rol, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields: object) -> UserModel:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, rol="admin", **extra_fields)


class UserModel(AbstractBaseUser, PermissionsMixin):
    class RolChoices(models.TextChoices):
        ADMIN = "admin", "Administrador"
        EXTERNO = "externo", "Externo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    rol = models.CharField(max_length=10, choices=RolChoices.choices, default=RolChoices.EXTERNO)
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserModelManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def to_domain(self) -> Usuario:
        return Usuario(
            id=self.id,
            email=EmailAddress(self.email),
            password_hash=PasswordHash(self.password),
            rol=UserRole(self.rol),
            nombre=self.nombre,
            apellido=self.apellido,
            activo=self.activo,
        )

    def __str__(self) -> str:
        return f"{self.email} ({self.rol})"
