from notifications.services.template_loading import JsonTemplateLoader


json_loader = JsonTemplateLoader()
json_loader.register_template_path("projects/notifications.json")
