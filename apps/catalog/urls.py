from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # Tipos
    path("tipos/", views.TipoListView.as_view(), name="tipo_list"),
    path("tipos/nuevo/", views.TipoCreateView.as_view(), name="tipo_create"),
    path("tipos/<int:pk>/editar/", views.TipoUpdateView.as_view(), name="tipo_update"),
    path("tipos/<int:pk>/eliminar/", views.TipoDeleteView.as_view(), name="tipo_delete"),
    # Vitrinas
    path("vitrinas/", views.VitrinaListView.as_view(), name="vitrina_list"),
    path("vitrinas/nueva/", views.VitrinaCreateView.as_view(), name="vitrina_create"),
    path("vitrinas/<int:pk>/editar/", views.VitrinaUpdateView.as_view(), name="vitrina_update"),
    path("vitrinas/<int:pk>/eliminar/", views.VitrinaDeleteView.as_view(), name="vitrina_delete"),
]
