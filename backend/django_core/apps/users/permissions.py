from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(BasePermission):
    """Only admin rol users are allowed."""

    message = "Admin role required."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return (
            request.user
            and request.user.is_authenticated
            and request.user.activo
            and request.user.rol == "admin"
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Admin: all methods.
    Externo (authenticated): GET only.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user.activo
        return request.user.activo and request.user.rol == "admin"
