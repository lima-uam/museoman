import os

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from .state import State


class ActiveItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)


class AllItemManager(models.Manager):
    pass


class Item(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="nombre")
    identificador = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="identificador")
    estado = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.LIBRE,
        verbose_name="estado",
    )
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_items",
        verbose_name="usuario asignado",
    )
    observaciones = models.TextField(blank=True, verbose_name="observaciones")
    tipo = models.ForeignKey(
        "catalog.Tipo",
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="tipo",
    )
    vitrina = models.ForeignKey(
        "catalog.Vitrina",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name="vitrina",
    )
    activo = models.BooleanField(default=True, verbose_name="activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="fecha de creación")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_items",
        verbose_name="creado por",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="última modificación")

    # Default manager: active only
    objects = ActiveItemManager()
    # Manager that includes inactive items
    all_objects = AllItemManager()

    class Meta:
        verbose_name = "pieza"
        verbose_name_plural = "piezas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["assigned_user"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["vitrina"]),
            models.Index(fields=["activo"]),
        ]

    def __str__(self):
        return f"{self.identificador} — {self.nombre}"

    @cached_property
    def state_label(self):
        return State(self.estado).label


def _photo_upload_path(instance, filename):
    return f"items/{instance.item_id}/{filename}"


class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="photos", verbose_name="pieza")
    image = models.ImageField(upload_to=_photo_upload_path, verbose_name="imagen")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="fecha de subida")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_photos",
        verbose_name="subida por",
    )

    class Meta:
        verbose_name = "foto"
        verbose_name_plural = "fotos"
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Foto de {self.item}"

    def delete(self, *args, **kwargs):
        # Remove file from disk when record is deleted
        path = self.image.path if self.image else None
        super().delete(*args, **kwargs)
        if path and os.path.exists(path):
            os.remove(path)
