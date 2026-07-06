from django.contrib import admin

from .models import MonedaModel, ProductoModel, ProductoPrecioModel


class ProductoPrecioInline(admin.TabularInline):
    model = ProductoPrecioModel
    extra = 1


@admin.register(ProductoModel)
class ProductoModelAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "empresa", "activo", "created_at")
    list_filter = ("activo", "empresa")
    search_fields = ("codigo", "nombre")
    inlines = [ProductoPrecioInline]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(MonedaModel)
class MonedaModelAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "simbolo", "activo")
