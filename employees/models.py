from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    )
    title = models.CharField(max_length=100)
    description = models.TextField()
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    password_changed_at = models.DateTimeField(default=timezone.now)  # initially now
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"profile:{self.user.username}"

# OTP model for password reset
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_otps')
    otp = models.CharField(max_length=6)  # 6-digit OTP as string
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.email} - used:{self.used}"

# Email verification token model
class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"EmailToken {self.token} for {self.user.email}"