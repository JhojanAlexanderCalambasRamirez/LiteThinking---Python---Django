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


def _auto_codigo(nombre: str, empresa_id: str) -> str:
    prefix = "".join(c for c in nombre.upper() if c.isalnum())[:3] or "PRD"
    count = ProductoModel.objects.filter(empresa_id=empresa_id).count() + 1
    candidate = f"{prefix}-{count:03d}"
    while ProductoModel.objects.filter(codigo=candidate, empresa_id=empresa_id).exists():
        count += 1
        candidate = f"{prefix}-{count:03d}"
    return candidate


class ProductoSerializer(serializers.ModelSerializer):
    precios = ProductoPrecioSerializer(many=True, read_only=True)
    empresa_nit = serializers.CharField(source="empresa_id")
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)

    class Meta:
        model = ProductoModel
        fields = [
            "id", "codigo", "nombre", "caracteristicas",
            "empresa_nit", "empresa_nombre", "activo", "precios", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "precios", "empresa_nombre"]


class ProductoCreateSerializer(serializers.ModelSerializer):
    empresa_nit = serializers.CharField(source="empresa_id", write_only=True)
    codigo = serializers.CharField(required=False, allow_blank=True, default="")
    precios = ProductoPrecioSerializer(many=True, required=False)

    class Meta:
        model = ProductoModel
        fields = ["codigo", "nombre", "caracteristicas", "empresa_nit", "precios"]

    def create(self, validated_data: dict) -> ProductoModel:
        precios_data = validated_data.pop("precios", [])
        codigo = validated_data.get("codigo", "").strip().upper()
        if not codigo:
            validated_data["codigo"] = _auto_codigo(
                validated_data["nombre"], validated_data["empresa_id"]
            )
        else:
            validated_data["codigo"] = codigo
        producto = ProductoModel.objects.create(**validated_data)
        for precio_data in precios_data:
            ProductoPrecioModel.objects.create(
                producto=producto,
                moneda_id=precio_data["moneda_id"],
                precio=precio_data["precio"],
            )
        return producto
