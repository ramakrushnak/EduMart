"""Audit app - Logging and compliance"""
from django.db import models
import uuid
import json
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser


# ==================== MODELS ====================
class AuditLog(models.Model):
    """Audit trail for user actions"""
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, related_name='audit_logs', null=True, db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['resource_type', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f"{self.action} - {self.resource_type} by {self.user}"


class KafkaEventLog(models.Model):
    """Kafka event log for audit trail and replay"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    topic = models.CharField(max_length=100, db_index=True)
    partition = models.PositiveIntegerField()
    offset = models.PositiveBigIntegerField()
    event_type = models.CharField(max_length=100, db_index=True)
    event_data = models.JSONField()
    idempotency_key = models.CharField(max_length=100, blank=True, null=True, db_index=True, unique=True)
    status = models.CharField(max_length=20, default='PENDING', db_index=True)
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'kafka_event_logs'
        ordering = ['-timestamp']
        verbose_name = 'Kafka Event Log'
        verbose_name_plural = 'Kafka Event Logs'
        indexes = [
            models.Index(fields=['topic', 'partition', 'offset']),
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.event_id}"


# ==================== SERIALIZERS ====================
class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user_email', 'action', 'resource_type', 'resource_id', 'changes', 'created_at']
        read_only_fields = fields


class KafkaEventLogSerializer(serializers.ModelSerializer):
    """Kafka event log serializer"""
    class Meta:
        model = KafkaEventLog
        fields = ['id', 'event_id', 'topic', 'event_type', 'status', 'timestamp', 'created_at', 'processed_at']
        read_only_fields = fields


# ==================== VIEWS ====================
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log viewing (admin only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['action', 'resource_type', 'user']
    search_fields = ['resource_id', 'user__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class KafkaEventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Kafka event log viewing (admin only)"""
    queryset = KafkaEventLog.objects.all()
    serializer_class = KafkaEventLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['topic', 'event_type', 'status']
    search_fields = ['event_id']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
