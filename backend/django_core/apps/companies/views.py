from __future__ import annotations

from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.permissions import IsAdmin, IsAdminOrReadOnly
from utils.blockchain import log_blockchain

from .models import EmpresaModel
from .serializers import EmpresaListSerializer, EmpresaSerializer


class EmpresaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):  # type: ignore[override]
        qs = EmpresaModel.objects.all()
        if not (self.request.user.is_authenticated and self.request.user.rol == "admin"):
            qs = qs.filter(activo=True)
        return qs

    def get_serializer_class(self):  # type: ignore[override]
        if self.request.method == "GET":
            return EmpresaListSerializer
        return EmpresaSerializer

    def perform_create(self, serializer: EmpresaSerializer) -> None:  # type: ignore[override]
        empresa = serializer.save()
        log_blockchain(
            "empresa",
            empresa.nit,
            "CREATE",
            {"nit": empresa.nit, "nombre": empresa.nombre},
        )


class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmpresaModel.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "nit"

    def perform_update(self, serializer: EmpresaSerializer) -> None:  # type: ignore[override]
        empresa = serializer.save()
        log_blockchain(
            "empresa",
            empresa.nit,
            "UPDATE",
            {"nit": empresa.nit, "nombre": empresa.nombre},
        )

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=["activo", "updated_at"])
        log_blockchain(
            "empresa",
            instance.nit,
            "DELETE",
            {"nit": instance.nit, "nombre": instance.nombre},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
