import sys
import time

from django.apps import AppConfig

from config.utils.utils import is_server_command


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'

    def ready(self):
        from .notifications import signals

        if 'manage.py' in sys.argv[0] and not is_server_command():
            return

        import logging
        from .notifications.loaders import json_loader
        logger = logging.getLogger('django')

        try:
            start_time = time.perf_counter()
            logger.info('Loading JSON notification templates for <projects> app started.')

            loaded_templates = json_loader.load_templates()

            for template_name, _ in loaded_templates.items():
                logger.info(f"Template <{template_name}> loaded successfully")

            execution_time = time.perf_counter() - start_time
            logger.info(
                f"JSON templates loading completed successfully. "
                f"Loaded {len(loaded_templates)} templates. "
                f"Execution time: {execution_time:.2f} seconds."
            )

        except Exception as e:
            logger.error(f"Failed to load templates with error: {e}")
            raise