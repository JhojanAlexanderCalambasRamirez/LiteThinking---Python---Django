from django.urls import path

from .views import MonedaListView, ProductoDetailView, ProductoListCreateView, ProductoPrecioView

urlpatterns = [
    path("productos/", ProductoListCreateView.as_view(), name="producto-list-create"),
    path("productos/<uuid:id>/", ProductoDetailView.as_view(), name="producto-detail"),
    path("productos/<uuid:producto_id>/precios/", ProductoPrecioView.as_view(), name="producto-precio"),
    path("monedas/", MonedaListView.as_view(), name="moneda-list"),
]
