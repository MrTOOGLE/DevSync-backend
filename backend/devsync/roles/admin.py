from django.contrib import admin

from roles.models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "rank", "color")
    search_fields = ["name", "project__title"]
    list_filter = ("project", )

    save_on_top = True
