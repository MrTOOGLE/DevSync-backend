from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


User = get_user_model()


class Role(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey("projects.Project", related_name='roles', on_delete=models.CASCADE)
    color = models.CharField(max_length=7, default="#000000")
    rank = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])

    def __str__(self):
        return f'Role {self.name} (id: {self.id})'


class MemberRole(models.Model):
    role = models.ForeignKey(Role, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.role} for {self.user}'


"""class RolePermissions(models.Model):
    role = models.OneToOneField(Role, related_name='permissions', on_delete=models.CASCADE)
    all_permissions = models.BooleanField(default=False)
    manage_project = models.BooleanField(default=False)
    manage_members = models.BooleanField(default=False)
    manage_members_in_department = models.BooleanField(default=False)
    manage_roles = models.BooleanField(default=False)
    manage_roles_in_department = models.BooleanField(default=False)
    assign_roles = models.BooleanField(default=False)
    assign_roles_in_department = models.BooleanField(default=False)
    manage_departments = models.BooleanField(default=False)
    manage_department = models.BooleanField(default=False)
    manage_tasks = models.BooleanField(default=False)
    manage_tasks_in_department = models.BooleanField(default=False)
    add_tasks = models.BooleanField(default=True)
    add_tasks_in_department = models.BooleanField(default=True)
    manage_votings = models.BooleanField(default=False)
    add_voting = models.BooleanField(default=True)
    vote_in_voting = models.BooleanField(default=True)
    manage_comments = models.BooleanField(default=False)
    view_audit = models.BooleanField(default=False)

    def __str__(self):
        return f"Permissions for {self.role.name} ({self.role.project})"""
