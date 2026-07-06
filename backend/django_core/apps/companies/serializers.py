import re

from rest_framework import serializers

from .models import EmpresaModel

_NIT_PATTERN = re.compile(r"^\d{6,10}(-\d)?$")
_TELEFONO_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModel
        fields = ["nit", "nombre", "direccion", "telefono", "activo", "created_at", "updated_at"]
        read_only_fields = ["activo", "created_at", "updated_at"]

    def validate_nit(self, value: str) -> str:
        cleaned = value.strip()
        if not _NIT_PATTERN.match(cleaned):
            raise serializers.ValidationError(
                "NIT inválido. Formato: 6-10 dígitos, opcionalmente '-' + dígito verificador. Ej: 900123456-7"
            )
        return cleaned

    def update(self, instance: EmpresaModel, validated_data: dict) -> EmpresaModel:
        new_nit = validated_data.pop("nit", None)
        if new_nit and new_nit != instance.nit:
            EmpresaModel.objects.filter(nit=instance.nit).update(nit=new_nit)
            instance = EmpresaModel.objects.get(nit=new_nit)
        return super().update(instance, validated_data)

    def validate_nombre(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value.strip()

    def validate_telefono(self, value: str) -> str:
        if not _TELEFONO_PATTERN.match(value.strip()):
            raise serializers.ValidationError(
                "Teléfono inválido. Use formato internacional: +57 601 234 5678"
            )
        return value.strip()


class EmpresaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModel
        fields = ["nit", "nombre", "direccion", "telefono", "activo"]
