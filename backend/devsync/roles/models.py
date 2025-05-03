from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

User = get_user_model()


class Role(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey("projects.Project", related_name='roles', on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default="#000000")
    rank = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    permissions = models.ManyToManyField("RolePermission")
    is_everyone = models.BooleanField(default=False)

    def __str__(self):
        return f'Role {self.name} (id: {self.id})'


class MemberRole(models.Model):
    role = models.ForeignKey(Role, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.role} ({self.user})'


class RolePermission(models.Model):
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField(max_length=1256)

    def __str__(self):
        return f"{self.name} ({self.codename})"
