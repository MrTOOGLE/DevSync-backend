from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from .fields import WEBPField


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_email_verified", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    avatar = WEBPField(upload_to="users/%Y/%m/%d/", blank=True, null=True, verbose_name="Аватар")
    city = models.CharField(max_length=50, blank=False, default="Москва")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["last_name", "first_name", "city"]

    objects = CustomUserManager()

    @property
    def username(self):
        return self.get_username()

    def verify_email(self):
        self.is_email_verified = True
        self.save()

    def __str__(self):
        return f"{self.last_name} {self.first_name} (id: {self.pk})"
