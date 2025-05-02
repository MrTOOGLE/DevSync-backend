from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active", "city")
    list_filter = ("is_staff", "is_active")
    ordering = ("email",)
    search_fields = ("email__startswith", "first_name__startswith", "last_name__startswith")

    fieldsets = (
        (None, {"fields": ("email", "password", "is_email_verified")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "avatar", "is_active", "is_staff"),
        }),
    )

    save_on_top = True
