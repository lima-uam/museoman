from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["item", "action", "actor", "from_state", "to_state", "created_at"]
    list_filter = ["action"]
    search_fields = ["item__nombre", "item__identificador"]
    readonly_fields = ["item", "actor", "action", "from_state", "to_state", "payload", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
