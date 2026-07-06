from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import CustomTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth
    path("api/v1/auth/login/", CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Resources
    path("api/v1/", include("apps.companies.urls")),
    path("api/v1/", include("apps.products.urls")),
    path("api/v1/", include("apps.inventory.urls")),
    path("api/v1/", include("apps.users.urls")),
]
