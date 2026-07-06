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
    queryset = UserModel.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [IsAdmin]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = UserModel.objects.filter(activo=True)
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
