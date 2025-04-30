from django.contrib import admin
from .models import Project, ProjectMember, Department, MemberDepartment, Role, RolePermissions, ProjectInvitation


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "date_created")
    search_fields = ["title", "creator__email"]

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


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "department", "rank", "color")
    search_fields = ["name", "project__title", "department__title"]
    list_filter = ("project", "department")

    save_on_top = True


@admin.register(RolePermissions)
class RolePermissionsAdmin(admin.ModelAdmin):
    list_display = ("role", "manage_project", "manage_members", "manage_roles")
    list_filter = ("manage_project", "manage_members", "manage_roles")

    save_on_top = True
