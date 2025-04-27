import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from rest_framework.exceptions import ParseError

from notifications.services.templates import NotificationTemplate, NotificationTemplateAction


@runtime_checkable
class TemplateLoaderProtocol(Protocol):
    def load_templates(self) -> MappingProxyType[str, NotificationTemplate]:
        """Load and return all templates"""

    def get_template(self, name: str) -> NotificationTemplate:
        """Get specific template by name"""


_loaded_templates: dict[str, NotificationTemplate] = {}


def get_template(name: str) -> NotificationTemplate:
    if name in _loaded_templates:
        return _loaded_templates[name]
    raise KeyError(f'Template "{name}" not loaded.')


class JsonTemplateLoader:
    def __init__(self):
        self._templates: dict[str, NotificationTemplate] = {}
        self._templates_paths: list[Path] = []

    def register_template_path(self, template_path: str) -> None:
        """Register path to templates for specific app"""
        static_path = Path(static(template_path)[1:])
        if not static_path.exists():
            raise FileNotFoundError(f"Template path {static_path} does not exist")
        self._templates_paths.append(static_path)

    @lru_cache(maxsize=None)
    def load_templates(self) -> MappingProxyType[str, NotificationTemplate]:
        """Load all templates from registered paths"""
        for path in self._templates_paths:
            self._load_templates_from_path(path)
        return MappingProxyType(self._templates)

    def get_template(self, name: str) -> NotificationTemplate:
        """Get specific template by name"""
        if not self._templates:
            self.load_templates()
        try:
            return self._templates[name]
        except KeyError:
            raise ValueError(f"Template {name} not found")

    def _load_templates_from_path(self, path: Path) -> None:
        with open(path, 'r') as file:
            templates_data = json.load(file)

        for name, template_data in templates_data.items():
            self._templates[name] = self._parse_template(template_data, name)
            _loaded_templates[name] = self._templates[name]

    @classmethod
    def _parse_template(cls, template_dict: dict, template_name: str) -> NotificationTemplate:
        try:
            return NotificationTemplate(
                title=template_dict.get('title', 'null'),
                message=template_dict.get('message', 'null'),
                content_type=cls._parse_content_type(template_dict['content_type']),
                actions=tuple(cls._parse_actions(template_dict.get('actions', []), template_name)),
                footnote=template_dict.get('footnote', None),
            )
        except KeyError as e:
            raise ParseError(f"Missing required field {e} in template {template_name}")

    @classmethod
    def _parse_content_type(cls, content_type_str: str) -> ContentType:
        try:
            app_label, model = content_type_str.split(':')
            return ContentType.objects.get(app_label=app_label, model=model)
        except (ValueError, ContentType.DoesNotExist) as e:
            raise ParseError(f"Invalid content type: {str(e)}")

    @classmethod
    def _parse_actions(cls, actions: list[dict], template_name: str) -> list[NotificationTemplateAction]:
        return [cls._parse_action(action, template_name) for action in actions]

    @classmethod
    def _parse_action(cls, action: dict, template_name: str) -> NotificationTemplateAction:
        try:
            return NotificationTemplateAction(
                type=action.get('type'),
                text=action.get('text'),
                viewname=action.get('viewname'),
                viewname_kwargs=MappingProxyType(action.get('viewname_kwargs', {})),
                redirect=action.get('redirect'),
                redirect_kwargs=MappingProxyType(action.get('redirect_kwargs', {})),
                style=action.get('style'),
                next_template=action.get('next_template'),
                new_related_object_id=action.get('new_related_object_id')
            )
        except KeyError as e:
            raise ParseError(f"Missing required field {e} in action for template {template_name}")
