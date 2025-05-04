from notifications.services.template_loading import JsonNotificationTemplateLoader


json_loader = JsonNotificationTemplateLoader()
json_loader.register_template_path("projects/notifications.json")
