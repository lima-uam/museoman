from django.contrib import admin

from .models import Tipo, Vitrina


@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "created_at"]
    search_fields = ["nombre"]


@admin.register(Vitrina)
class VitrinaAdmin(admin.ModelAdmin):
    list_display = ["numero", "created_at"]
    ordering = ["numero"]
