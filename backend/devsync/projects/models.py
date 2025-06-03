from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

from config.utils.fields import WEBPField
from config.settings import PROJECT_INVITATION_EXPIRY_DAYS

User = get_user_model()


class PublicProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_public=True)


class Project(models.Model):
    title = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, related_name='created_projects', on_delete=models.CASCADE)
    description = models.CharField(max_length=1256, blank=True, default='')
    is_public = models.BooleanField(default=True)
    avatar = WEBPField(upload_to="projects/%Y/%m/%d/", blank=True, null=True, verbose_name="Аватар")

    objects = models.Manager()
    public_objects = PublicProjectManager()

    class Meta:
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"{self.title} (Owner: {self.owner})"


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='project_memberships', on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_member')
        ]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
        ]

    def __str__(self):
        return f'{self.user} - {self.project}'


class ProjectInvitation(models.Model):
    project = models.ForeignKey(Project, related_name='invitations', on_delete=models.CASCADE)
    user = models.ForeignKey(User,related_name='project_invitations',on_delete=models.CASCADE)
    invited_by = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'user'],
                name='unique_project_user_invitation'
            ),
        ]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['project']),
        ]
        ordering = ['-date_created']

    def is_expired(self):
        return now() >= self.date_created + timedelta(days=PROJECT_INVITATION_EXPIRY_DAYS)

    def accept(self) -> None:
        ProjectMember.objects.get_or_create(project=self.project, user=self.user)
        self.delete()

    def reject(self) -> None:
        self.delete()

    def __str__(self):
        return f'Invitation to {self.project} for {self.user}'


class Department(models.Model):
    project = models.ForeignKey(Project, related_name='departments', on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=256, blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['project']),
        ]

    def __str__(self):
        return f'{self.title} ({self.project})'


class MemberDepartment(models.Model):
    department = models.ForeignKey(Department, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='department_memberships', on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['department', 'user'], name='unique_department_member')
        ]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['department']),
        ]


    def __str__(self):
        return f'{self.user} - {self.department}'


class Task(models.Model):
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    department = models.ForeignKey(Department, related_name='tasks', on_delete=models.CASCADE, null=True, blank=True)
    assignees = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f'Task {self.title[:30]} ({self.project.title})'


@receiver(post_save, sender=Project)
def add_owner_as_member(sender, instance, created, **kwargs):
    if created:
        ProjectMember(
            project=instance,
            user=instance.owner
        ).save()
