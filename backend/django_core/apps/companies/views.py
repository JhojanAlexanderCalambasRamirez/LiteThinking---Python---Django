from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin, IsAdminOrReadOnly

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


class EmpresaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmpresaModel.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = "nit"

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=["activo", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)
