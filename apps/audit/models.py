from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_STATE_CHANGE = "state_change"
    ACTION_ASSIGNED = "assigned"
    ACTION_DEACTIVATED = "deactivated"
    ACTION_ACTIVATED = "activated"
    ACTION_PHOTO_ADDED = "photo_added"
    ACTION_PHOTO_DELETED = "photo_deleted"
    ACTION_CREATED = "created"
    ACTION_UPDATED = "updated"
    ACTION_VITRINA_CREATED = "vitrina_created"
    ACTION_VITRINA_UPDATED = "vitrina_updated"
    ACTION_VITRINA_DELETED = "vitrina_deleted"

    ACTION_CHOICES = [
        (ACTION_STATE_CHANGE, "Cambio de estado"),
        (ACTION_ASSIGNED, "Asignación"),
        (ACTION_DEACTIVATED, "Desactivación"),
        (ACTION_ACTIVATED, "Activación"),
        (ACTION_PHOTO_ADDED, "Foto añadida"),
        (ACTION_PHOTO_DELETED, "Foto eliminada"),
        (ACTION_CREATED, "Creación"),
        (ACTION_UPDATED, "Edición"),
        (ACTION_VITRINA_CREATED, "Vitrina creada"),
        (ACTION_VITRINA_UPDATED, "Vitrina editada"),
        (ACTION_VITRINA_DELETED, "Vitrina eliminada"),
    ]

    item = models.ForeignKey(
        "items.Item",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="pieza",
    )
    vitrina = models.ForeignKey(
        "catalog.Vitrina",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="vitrina",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
        verbose_name="usuario",
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name="acción")
    field = models.CharField(max_length=64, blank=True, default="", verbose_name="campo")
    from_state = models.CharField(max_length=255, blank=True, verbose_name="valor anterior")
    to_state = models.CharField(max_length=255, blank=True, verbose_name="valor nuevo")
    payload = models.JSONField(default=dict, blank=True, verbose_name="datos")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="fecha")

    class Meta:
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["item", "-created_at"])]

    def __str__(self):
        return f"{self.get_action_display()} — {self.item} — {self.created_at:%Y-%m-%d %H:%M}"
