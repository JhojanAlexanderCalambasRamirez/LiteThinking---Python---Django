from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.users.models import UserModel

USERS = [
    {
        "email": "admin@litethinking.com",
        "password": "Admin1234!",
        "rol": "admin",
        "nombre": "Administrador",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "externo@litethinking.com",
        "password": "Externo1234!",
        "rol": "externo",
        "nombre": "Externo",
        "is_staff": False,
        "is_superuser": False,
    },
]


class Command(BaseCommand):
    help = "Create default admin and external users for evaluation."

    def handle(self, *args: object, **kwargs: object) -> None:
        for data in USERS:
            email = data["email"]
            if UserModel.objects.filter(email=email).exists():
                self.stdout.write(f"  Ya existe: {email}")
                continue
            UserModel.objects.create_user(
                email=email,
                password=data["password"],
                rol=data["rol"],
                nombre=data["nombre"],
                is_staff=data["is_staff"],
                is_superuser=data["is_superuser"],
            )
            self.stdout.write(self.style.SUCCESS(f"  Creado: {email} ({data['rol']})"))

        self.stdout.write(self.style.SUCCESS("seed_users completado."))
