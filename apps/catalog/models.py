from django.db import models


class Tipo(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="nombre")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "tipo"
        verbose_name_plural = "tipos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Vitrina(models.Model):
    numero = models.PositiveIntegerField(unique=True, verbose_name="número")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "vitrina"
        verbose_name_plural = "vitrinas"
        ordering = ["numero"]

    def __str__(self):
        return f"Vitrina {self.numero}"
