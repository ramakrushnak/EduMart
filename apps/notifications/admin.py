"""Django admin for notifications"""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'category', 'is_read', 'created_at']
    list_filter = ['notification_type', 'category', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['id', 'created_at']
    fieldsets = (
        ('Notification Info', {'fields': ('id', 'user', 'notification_type', 'category')}),
        ('Content', {'fields': ('title', 'message', 'description')}),
        ('Status', {'fields': ('is_read', 'read_at')}),
        ('Dates', {'fields': ('created_at', 'expires_at')}),
        ('Reference', {'fields': ('related_object_id',)}),
    )
    date_hierarchy = 'created_at'
