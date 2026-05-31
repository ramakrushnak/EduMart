"""Django admin configuration for accounts"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, School, UserEmailVerification, TokenBlacklist


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'type', 'city', 'is_active', 'created_at']
    list_filter = ['type', 'city', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'school', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'school', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'mobile']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login', 'date_joined']
    fieldsets = (
        ('Personal Info', {'fields': ('id', 'email', 'username', 'first_name', 'last_name', 'mobile')}),
        ('Address', {'fields': ('address', 'city', 'state', 'postal_code', 'country')}),
        ('School & Role', {'fields': ('school', 'role')}),
        ('Status', {'fields': ('is_email_verified', 'is_mobile_verified', 'is_active')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('created_at', 'updated_at', 'last_login', 'date_joined')}),
    )


@admin.register(UserEmailVerification)
class UserEmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'created_at', 'expires_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'token', 'created_at']


@admin.register(TokenBlacklist)
class TokenBlacklistAdmin(admin.ModelAdmin):
    list_display = ['user', 'blacklisted_at', 'expires_at']
    list_filter = ['blacklisted_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'token', 'blacklisted_at']
