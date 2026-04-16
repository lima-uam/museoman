from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("usuarios/", views.UserListView.as_view(), name="user_list"),
    path("usuarios/nuevo/", views.UserCreateView.as_view(), name="user_create"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="user_update"),
]
