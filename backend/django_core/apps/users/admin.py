from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UserModel


@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    list_display = ("email", "nombre", "apellido", "rol", "activo", "created_at")
    list_filter = ("rol", "activo")
    search_fields = ("email", "nombre", "apellido")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("nombre", "apellido")}),
        ("Permisos", {"fields": ("rol", "activo", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "rol", "nombre", "apellido"),
        }),
    )
