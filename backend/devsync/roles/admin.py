from django.contrib import admin

from roles.models import Role, RolePermission, MemberRole


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "rank", "color")
    search_fields = ["name", "project__title"]
    list_filter = ("project", )

    save_on_top = True


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'category', 'description')
    search_fields = ['codename']


@admin.register(MemberRole)
class MemberRoleAdmin(admin.ModelAdmin):
    list_display = ('role', 'user')
