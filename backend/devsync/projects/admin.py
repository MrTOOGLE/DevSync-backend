from django.contrib import admin
from .models import Project, ProjectMember, Department, MemberDepartment, ProjectInvitation


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "date_created")
    search_fields = ["title", "owner__email"]

    save_on_top = True


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "date_joined")
    search_fields = ["project__title", "user__email"]

    save_on_top = True


@admin.register(ProjectInvitation)
class ProjectInvitationAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "invited_by")
    save_on_top = True

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "date_created")
    search_fields = ["title", "project__title"]
    list_filter = ("date_created",)

    save_on_top = True


@admin.register(MemberDepartment)
class DepartmentMemberAdmin(admin.ModelAdmin):
    list_display = ("department", "user", "date_joined")
    search_fields = ["department__title", "user__email"]

    save_on_top = True
