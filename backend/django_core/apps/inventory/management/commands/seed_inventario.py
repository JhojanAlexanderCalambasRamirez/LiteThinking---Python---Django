from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.inventory.models import InventarioModel
from apps.products.models import ProductoModel


class Command(BaseCommand):
    help = "Create inventory entries (cantidad=1) for products that lack one."

    def handle(self, *args: object, **kwargs: object) -> None:
        productos = ProductoModel.objects.filter(activo=True)
        created = 0
        for producto in productos:
            _, was_created = InventarioModel.objects.get_or_create(
                producto=producto,
                defaults={"cantidad": 1},
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Done: {created} inventory entries created."))
