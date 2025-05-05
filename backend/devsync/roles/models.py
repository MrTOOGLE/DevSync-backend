from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from projects.models import Project

User = get_user_model()


class Role(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey("projects.Project", related_name='roles', on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default="#000000")
    rank = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])
    is_everyone = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-rank', )

    def __str__(self):
        return f'Role {self.name} (id: {self.id})'


class MemberRole(models.Model):
    role = models.ForeignKey(Role, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'user'],
                name='unique_member_role'
            )
        ]

    def __str__(self):
        return f'{self.role} ({self.user})'


class RolePermission(models.Model):
    role = models.ForeignKey(Role, related_name='permissions', on_delete=models.CASCADE)
    permission = models.ForeignKey('Permission', to_field='codename', on_delete=models.CASCADE)
    value = models.BooleanField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'permission'],
                name='unique_role_permission'
            )
        ]

    def __str__(self):
        return f'{self.role} ({self.permission})'


class StaticPermissionManager(models.Manager):
    _cached_permissions = None

    def get_queryset(self):
        if StaticPermissionManager._cached_permissions is None:
            qs = super().get_queryset()
            StaticPermissionManager._cached_permissions = list(qs)
            return qs
        return super().get_queryset()

    @classmethod
    def cached(cls) -> list['Permission']:
        if cls._cached_permissions is None:
            cls._cached_permissions = list(Permission.objects.all())
        return cls._cached_permissions


class Permission(models.Model):
    codename = models.SlugField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField(max_length=1256)
    default_value = models.BooleanField(default=False)

    objects = StaticPermissionManager()

    class Meta:
        ordering = ('codename',)

    def __str__(self):
        return f"{self.name} ({self.codename})"


@receiver(signal=post_save, sender=Project)
def init_everyone_role(sender, instance, created, **kwargs):
    if not created:
        return

    from roles.services.services import create_everyone_role

    create_everyone_role(instance.id).save()
