from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import UserModel
from .permissions import IsAdmin
from .serializers import CustomTokenObtainPairSerializer, RegisterUserSerializer, UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterUserView(generics.CreateAPIView):
    """
    Public: registers as 'externo' (rol forced, cannot self-assign admin).
    Admin: can register any role by passing rol=admin.
    """
    queryset = UserModel.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):  # type: ignore[override]
        return RegisterUserSerializer

    def perform_create(self, serializer):  # type: ignore[override]
        is_admin_request = (
            self.request.user.is_authenticated
            and getattr(self.request.user, "rol", None) == "admin"
        )
        if not is_admin_request:
            serializer.save(rol="externo")
        else:
            serializer.save()


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = UserModel.objects.filter(activo=True)
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
