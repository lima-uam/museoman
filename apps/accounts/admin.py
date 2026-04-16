from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "name", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_active"]
    search_fields = ["email", "name"]
    ordering = ["name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("name",)}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "password1", "password2", "is_staff"),
            },
        ),
    )
    readonly_fields = ["last_login", "date_joined"]
