from django.urls import path

from .views import CurrentUserView, RegisterUserView, UserListView

urlpatterns = [
    path("users/me/", CurrentUserView.as_view(), name="current-user"),
    path("users/register/", RegisterUserView.as_view(), name="register-user"),
    path("users/", UserListView.as_view(), name="user-list"),
]
