from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html

from notifications.models import NotificationContextObject, Notification


class NotificationContextObjectInline(GenericTabularInline):
    model = NotificationContextObject
    extra = 0
    fields = ('name', 'content_type', 'object_id', 'content_object')
    readonly_fields = ('content_object',)
    ct_field = 'content_type'
    ct_fk_field = 'object_id'

    def has_add_permission(self, request, obj=None):
        return False  # Запрещаем добавление новых объектов через админку


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_email',
        'truncated_title',
        'formatted_message_display',
        'is_read',
        'is_hidden',
        'created_at',
        'content_object_link',
    )
    list_filter = (
        'is_read',
        'is_hidden',
        'created_at',
        'content_type',
    )
    search_fields = (
        'user__email',
        'title',
        'message',
    )
    list_select_related = ('user', 'content_type')
    readonly_fields = (
        'formatted_message_display',
        'created_at',
        'content_object_link',
        'actions_data_prettified',
    )
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'message', 'formatted_message_display')
        }),
        ('Status', {
            'fields': ('is_read', 'is_hidden', 'footnote')
        }),
        ('Metadata', {
            'fields': ('content_object_link', 'actions_data_prettified', 'created_at')
        }),
    )
    inlines = (NotificationContextObjectInline,)
    actions = ('mark_as_read', 'mark_as_unread', 'hide_notifications')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def truncated_title(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    truncated_title.short_description = 'Title'

    def formatted_message_display(self, obj):
        return obj.formatted_message
    formatted_message_display.short_description = 'Formatted Message'

    def content_object_link(self, obj):
        if not obj.content_object:
            return "-"
        url = admin_url(obj.content_object)
        return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
    content_object_link.short_description = 'Linked Object'

    def actions_data_prettified(self, obj):
        import json
        return format_html('<pre>{}</pre>', json.dumps(obj.actions_data, indent=2))
    actions_data_prettified.short_description = 'Actions Data'

    @admin.action(description='Mark selected as read')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected as unread')
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    @admin.action(description='Hide selected notifications')
    def hide_notifications(self, request, queryset):
        queryset.update(is_hidden=True)


def admin_url(obj):
    from django.urls import reverse
    meta = obj._meta
    return reverse(f'admin:{meta.app_label}_{meta.model_name}_change', args=[obj.pk])


@admin.register(NotificationContextObject)
class NotificationContextObjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'notification_link', 'name', 'content_object_link')
    list_filter = ('name',)
    search_fields = ('notification__title', 'name')
    readonly_fields = ('notification_link', 'content_object_link')

    def notification_link(self, obj):
        url = admin_url(obj.notification)
        return format_html('<a href="{}">{}</a>', url, str(obj.notification))
    notification_link.short_description = 'Notification'

    def content_object_link(self, obj):
        if not obj.content_object:
            return "-"
        url = admin_url(obj.content_object)
        return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
    content_object_link.short_description = 'Content Object'