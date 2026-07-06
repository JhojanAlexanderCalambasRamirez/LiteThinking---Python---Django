from decimal import Decimal

from rest_framework import serializers

from .models import MonedaModel, ProductoModel, ProductoPrecioModel


class MonedaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonedaModel
        fields = ["codigo", "nombre", "simbolo"]


class ProductoPrecioSerializer(serializers.ModelSerializer):
    moneda_codigo = serializers.CharField(source="moneda_id")
    moneda_nombre = serializers.CharField(source="moneda.nombre", read_only=True)
    moneda_simbolo = serializers.CharField(source="moneda.simbolo", read_only=True)

    class Meta:
        model = ProductoPrecioModel
        fields = ["id", "moneda_codigo", "moneda_nombre", "moneda_simbolo", "precio"]
        read_only_fields = ["id"]

    def validate_precio(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value


class ProductoSerializer(serializers.ModelSerializer):
    precios = ProductoPrecioSerializer(many=True, read_only=True)
    empresa_nit = serializers.CharField(source="empresa_id")

    class Meta:
        model = ProductoModel
        fields = [
            "id", "codigo", "nombre", "caracteristicas",
            "empresa_nit", "activo", "precios", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "activo", "created_at", "updated_at", "precios"]

    def validate_codigo(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("El código no puede estar vacío.")
        return value.strip().upper()


class ProductoCreateSerializer(serializers.ModelSerializer):
    empresa_nit = serializers.CharField(source="empresa_id", write_only=True)
    precios = ProductoPrecioSerializer(many=True, required=False)

    class Meta:
        model = ProductoModel
        fields = ["codigo", "nombre", "caracteristicas", "empresa_nit", "precios"]

    def create(self, validated_data: dict) -> ProductoModel:
        precios_data = validated_data.pop("precios", [])
        producto = ProductoModel.objects.create(**validated_data)
        for precio_data in precios_data:
            ProductoPrecioModel.objects.create(
                producto=producto,
                moneda_id=precio_data["moneda_id"],
                precio=precio_data["precio"],
            )
        return producto
