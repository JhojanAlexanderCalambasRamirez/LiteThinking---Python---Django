import re

from rest_framework import serializers

from .models import EmpresaModel

_NIT_PATTERN = re.compile(r"^\d{6,10}(-\d)?$")


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModel
        fields = ["nit", "nombre", "direccion", "telefono", "activo", "created_at", "updated_at"]
        read_only_fields = ["activo", "created_at", "updated_at"]

    def validate_nit(self, value: str) -> str:
        if not _NIT_PATTERN.match(value.strip()):
            raise serializers.ValidationError(
                "NIT inválido. Formato esperado: 6-10 dígitos, opcionalmente seguidos de '-' y un dígito verificador."
            )
        return value.strip()

    def validate_nombre(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value.strip()


class EmpresaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModel
        fields = ["nit", "nombre", "telefono", "activo"]
