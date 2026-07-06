from rest_framework import serializers

from apps.products.serializers import ProductoSerializer

from .models import InventarioModel


class InventarioSerializer(serializers.ModelSerializer):
    producto_detail = ProductoSerializer(source="producto", read_only=True)
    empresa_nit = serializers.CharField(source="producto.empresa_id", read_only=True)
    empresa_nombre = serializers.CharField(source="producto.empresa.nombre", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = InventarioModel
        fields = [
            "id",
            "producto",
            "producto_detail",
            "empresa_nit",
            "empresa_nombre",
            "cantidad",
            "observaciones",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "empresa_nit", "empresa_nombre", "created_by_email", "created_at", "updated_at"]


class InventarioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventarioModel
        fields = ["producto", "cantidad", "observaciones"]

    def validate_cantidad(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("La cantidad no puede ser negativa.")
        return value
