from django.contrib import admin

from .models import Item, ItemPhoto


class ItemPhotoInline(admin.TabularInline):
    model = ItemPhoto
    extra = 0
    readonly_fields = ["uploaded_at", "uploaded_by"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["nombre", "estado", "assigned_user", "activo"]
    list_filter = ["estado", "tipos", "vitrina", "activo"]
    search_fields = ["nombre"]
    inlines = [ItemPhotoInline]
    readonly_fields = ["created_at", "created_by", "updated_at"]
