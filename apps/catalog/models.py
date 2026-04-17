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
    nombre = models.CharField(max_length=100, verbose_name="nombre", blank=True, default="")
    url = models.URLField(max_length=500, blank=True, default="", verbose_name="URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "vitrina"
        verbose_name_plural = "vitrinas"
        ordering = ["numero"]

    def __str__(self):
        if self.nombre:
            return f"Vitrina {self.numero} — {self.nombre}"
        return f"Vitrina {self.numero}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            from django.db.models import Max
            max_num = Vitrina.objects.aggregate(m=Max("numero"))["m"] or 0
            self.numero = max_num + 1
        super().save(*args, **kwargs)
