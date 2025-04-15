from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


User = get_user_model()


class Project(models.Model):
    title = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, related_name='created_projects', on_delete=models.CASCADE)
    description = models.CharField(max_length=1256, blank=True, default='')

    def __str__(self):
        return f"{self.title} (Owner: {self.creator})"


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='project_memberships', on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_member')
        ]

    def __str__(self):
        return f'{self.user} - {self.project}'


class Department(models.Model):
    project = models.ForeignKey(Project, related_name='departments', on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'title'], name='unique_project_department')
        ]

    def __str__(self):
        return f'{self.title} ({self.project})'


class DepartmentMember(models.Model):
    department = models.ForeignKey(Department, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='department_memberships', on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['department', 'user'], name='unique_department_member')
        ]

    def __str__(self):
        return f'{self.user} - {self.department}'


class Role(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, related_name='roles', on_delete=models.CASCADE)
    color = models.CharField(max_length=7)
    department = models.ForeignKey(Department, related_name='roles', on_delete=models.CASCADE, null=True, blank=True)
    rank = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])

    def __str__(self):
        return f'{self.name} (Project: {self.project.title}, Department: {self.department.title if self.department else "N/A"})'


class RolePermissions(models.Model):
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
        return f"Permissions for {self.role.name} ({self.role.project})"
