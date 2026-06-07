"""Notifications app - Email, SMS, Push notifications"""
from django.db import models
import uuid
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# ==================== MODELS ====================
class Notification(models.Model):
    """User notifications"""
    TYPE_CHOICES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
        ('IN_APP', 'In-App'),
    ]

    CATEGORY_CHOICES = [
        ('ORDER', 'Order'),
        ('PAYMENT', 'Payment'),
        ('SHIPPING', 'Shipping'),
        ('ACCOUNT', 'Account'),
        ('PROMOTION', 'Promotion'),
        ('SYSTEM', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications', db_index=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    description = models.TextField(blank=True, null=True)
    related_object_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['category', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# ==================== SERIALIZERS ====================
class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'category', 'title', 'message', 'is_read', 'created_at', 'expires_at']
        read_only_fields = fields


# ==================== VIEWS ====================
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification management"""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.none()

    def get_queryset(self):
        """Get user's notifications"""
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.update(is_read=True)
        return Response({'message': f'Marked {count} notifications as read'})

    @action(detail=True, methods=['delete'])
    def delete(self, request, pk=None):
        """Delete notification"""
        notification = self.get_object()
        notification.delete()
        return Response({'message': 'Notification deleted'})

    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        """Clear all notifications"""
        notifications = self.get_queryset()
        count = notifications.count()
        notifications.delete()
        return Response({'message': f'Cleared {count} notifications'})
