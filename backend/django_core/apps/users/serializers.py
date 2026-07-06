from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserModel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ["id", "email", "nombre", "apellido", "rol", "activo", "created_at"]
        read_only_fields = ["id", "created_at"]


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = UserModel
        fields = ["email", "password", "nombre", "apellido", "rol"]

    def create(self, validated_data: dict) -> UserModel:
        password = validated_data.pop("password")
        user = UserModel(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: UserModel):  # type: ignore[override]
        token = super().get_token(user)
        token["email"] = user.email
        token["rol"] = user.rol
        token["nombre"] = user.nombre_completo() if hasattr(user, "nombre_completo") else user.email
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        data["rol"] = self.user.rol  # type: ignore[attr-defined]
        data["email"] = self.user.email  # type: ignore[attr-defined]
        return data

    def nombre_completo(self) -> str:
        parts = filter(None, [self.user.nombre, self.user.apellido])  # type: ignore[attr-defined]
        return " ".join(parts) or self.user.email  # type: ignore[attr-defined]
