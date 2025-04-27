from notifications.services.template_loading import JsonTemplateLoader


loader = JsonTemplateLoader()
loader.register_template_path("projects/notifications.json")
