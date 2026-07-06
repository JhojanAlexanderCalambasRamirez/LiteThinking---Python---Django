from django.urls import path

from .views import EmpresaDetailView, EmpresaListCreateView

urlpatterns = [
    path("empresas/", EmpresaListCreateView.as_view(), name="empresa-list-create"),
    path("empresas/<str:nit>/", EmpresaDetailView.as_view(), name="empresa-detail"),
]
