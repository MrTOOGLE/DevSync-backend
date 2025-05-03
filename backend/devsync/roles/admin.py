from django.contrib import admin

from roles.models import Role, Permission, MemberRole, RolePermission


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "rank", "color")
    search_fields = ["name", "project__title"]
    list_filter = ("project", )
    readonly_fields = ('is_everyone', )
    save_on_top = True


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'category', 'description')
    search_fields = ['codename']

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission')


@admin.register(MemberRole)
class MemberRoleAdmin(admin.ModelAdmin):
    list_display = ('role', 'user')
