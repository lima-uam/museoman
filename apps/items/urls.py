from django.urls import path

from . import views

app_name = "items"

urlpatterns = [
    path("", views.ItemListView.as_view(), name="list"),
    path("nueva/", views.ItemCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ItemDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.ItemUpdateView.as_view(), name="update"),
    path("<int:pk>/transicion/", views.ItemTransitionView.as_view(), name="transition"),
    path("<int:pk>/asignar/", views.ItemAssignView.as_view(), name="assign"),
    path("<int:pk>/activar/", views.ItemDeactivateView.as_view(), name="deactivate"),
    path("<int:pk>/historial/", views.ItemAuditLogView.as_view(), name="audit_log"),
    path("<int:pk>/fotos/", views.PhotoUploadView.as_view(), name="photo_upload"),
    path("<int:pk>/fotos/<int:photo_pk>/eliminar/", views.PhotoDeleteView.as_view(), name="photo_delete"),
]
