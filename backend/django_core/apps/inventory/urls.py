from django.urls import path

from .views import (
    InventarioDetailView,
    InventarioListCreateView,
    export_and_email_inventory,
    export_pdf_inventory,
)

urlpatterns = [
    path("inventario/", InventarioListCreateView.as_view(), name="inventario-list-create"),
    path("inventario/export-email/", export_and_email_inventory, name="inventario-export-email"),
    path("inventario/export-pdf/", export_pdf_inventory, name="inventario-export-pdf"),
    path("inventario/<uuid:id>/", InventarioDetailView.as_view(), name="inventario-detail"),
]
