"""User and authentication models"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, URLValidator
import uuid


class School(models.Model):
    """School information for multi-tenancy"""
    SCHOOL_TYPES = [
        ('PRIMARY', 'Primary School'),
        ('SECONDARY', 'Secondary School'),
        ('SENIOR', 'Senior Secondary School'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    type = models.CharField(max_length=20, choices=SCHOOL_TYPES, default='PRIMARY')
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True, validators=[URLValidator()])
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schools'
        ordering = ['name']
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['city', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    """Extended user model with roles and school association"""
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('PARENT', 'Parent'),
        ('SCHOOL_ADMIN', 'School Admin'),
        ('SUPER_ADMIN', 'Super Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        validators=[MinLengthValidator(10)]
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT',
        db_index=True
    )
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
        db_index=True
    )
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default='India')
    profile_photo_url = models.URLField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    username = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['school', 'role']),
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role

    def is_admin(self):
        """Check if user is any type of admin"""
        return self.role in ['SCHOOL_ADMIN', 'SUPER_ADMIN']

    def is_school_admin(self):
        """Check if user is school admin"""
        return self.role == 'SCHOOL_ADMIN'

    def is_super_admin(self):
        """Check if user is super admin"""
        return self.role == 'SUPER_ADMIN'


class UserEmailVerification(models.Model):
    """Email verification tokens"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_email_verifications'
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'

    def __str__(self):
        return f"Email verification for {self.user.email}"


class TokenBlacklist(models.Model):
    """Blacklisted JWT tokens for logout functionality"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.TextField(unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_blacklist')
    blacklisted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'token_blacklist'
        verbose_name = 'Blacklisted Token'
        verbose_name_plural = 'Blacklisted Tokens'
        indexes = [
            models.Index(fields=['token', 'expires_at']),
            models.Index(fields=['user', 'blacklisted_at']),
        ]

    def __str__(self):
        return f"Blacklisted token for {self.user.email}"
