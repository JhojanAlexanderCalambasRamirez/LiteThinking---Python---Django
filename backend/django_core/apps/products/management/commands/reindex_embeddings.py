from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.products.models import ProductoModel
from apps.products.views import _index_product_embedding


class Command(BaseCommand):
    help = "Re-index embeddings for all active products in the AI agent service."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa",
            type=str,
            help="Only reindex products for this empresa NIT.",
        )

    def handle(self, *args, **options):
        qs = ProductoModel.objects.filter(activo=True)
        if options["empresa"]:
            qs = qs.filter(empresa_id=options["empresa"])

        total = qs.count()
        self.stdout.write(f"Indexing {total} products…")

        ok = 0
        for producto in qs.iterator():
            try:
                _index_product_embedding(producto)
                ok += 1
                self.stdout.write(f"  ✓ [{producto.codigo}] {producto.nombre}")
            except Exception as exc:
                self.stderr.write(f"  ✗ [{producto.codigo}] {exc}")

        self.stdout.write(self.style.SUCCESS(f"\nDone: {ok}/{total} indexed."))
