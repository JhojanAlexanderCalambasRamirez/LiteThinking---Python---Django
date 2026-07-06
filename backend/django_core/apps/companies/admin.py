from django.contrib import admin

from .models import EmpresaModel


@admin.register(EmpresaModel)
class EmpresaModelAdmin(admin.ModelAdmin):
    list_display = ("nit", "nombre", "telefono", "activo", "created_at")
    list_filter = ("activo",)
    search_fields = ("nit", "nombre")
    readonly_fields = ("created_at", "updated_at")
