"""Django admin for audit"""
from django.contrib import admin
from .models import AuditLog, KafkaEventLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action', 'resource_type', 'resource_id', 'created_at']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['user__email', 'resource_id']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(KafkaEventLog)
class KafkaEventLogAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'event_type', 'topic', 'status', 'timestamp']
    list_filter = ['event_type', 'topic', 'status', 'timestamp']
    search_fields = ['event_id', 'idempotency_key']
    readonly_fields = ['id', 'created_at', 'timestamp']
    date_hierarchy = 'timestamp'
