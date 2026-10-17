from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp')
    list_filter = ('action',)
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'timestamp', 'details', 'ip_address')
