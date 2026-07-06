from django.contrib import admin

from .models import InventarioModel


@admin.register(InventarioModel)
class InventarioModelAdmin(admin.ModelAdmin):
    list_display = ("producto", "get_empresa", "cantidad", "created_by", "created_at")
    list_filter = ("producto__empresa",)
    search_fields = ("producto__codigo", "producto__nombre")
    readonly_fields = ("id", "created_at", "updated_at")

    def get_empresa(self, obj: InventarioModel) -> str:
        return str(obj.producto.empresa)

    get_empresa.short_description = "Empresa"  # type: ignore[attr-defined]
