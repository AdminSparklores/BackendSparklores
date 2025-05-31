from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
from django.core.validators import RegexValidator
from django.conf import settings



phone_regex = RegexValidator(
    regex=r'^(?:\+62|62|0)8[1-9][0-9]{6,9}$',
    message="Masukkan nomor yang valid: contoh 081234567890 atau +6281234567890"
)

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=False, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class Address(models.Model):
    user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="addresses"
        )    
    label = models.CharField(max_length=255)
    full_address = models.TextField()
    notes = models.CharField(max_length=255, blank=True, null=True)
    recipient_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        help_text="Format yang diterima: 081234567890, 6281234567890, atau +6281234567890"
    )

    def __str__(self):
        return f"Address of {self.user.username}"

class OTPCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    @staticmethod
    def can_send_otp(email):
        now = timezone.now()
        one_minute_ago = now - timezone.timedelta(minutes=1)
        recent = OTPCode.objects.filter(email=email, created_at__gte=one_minute_ago)
        return not recent.exists()

    @staticmethod
    def too_many_requests(email):
        now = timezone.now()
        ten_minutes_ago = now - timezone.timedelta(minutes=10)
        return OTPCode.objects.filter(email=email, created_at__gte=ten_minutes_ago).count() >= 3

    @staticmethod
    def generate_otp():
        return str(random.randint(1000, 9999))