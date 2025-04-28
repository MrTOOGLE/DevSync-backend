import json
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from django.templatetags.static import static
from rest_framework.exceptions import ParseError

from notifications.services.schemes import TemplateSchema, TemplateActionSchema
from notifications.services.templates import NotificationTemplate, NotificationActionTemplate


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
            validated_scheme = TemplateSchema(**template_dict)
            app, model = validated_scheme.content_type.split(':')
            return NotificationTemplate(
                title=validated_scheme.title,
                message=validated_scheme.message,
                content_type_app=app,
                content_type_model=model,
                actions=tuple(cls._parse_actions(validated_scheme.actions)),
                footnote=validated_scheme.footnote,
            )
        except Exception as e:
            raise ParseError(f"Invalid template {template_name}: {str(e)}")

    @classmethod
    def _parse_actions(cls, actions: list[TemplateActionSchema]) -> list[NotificationActionTemplate]:
        return [cls._parse_action(action) for action in actions]

    @classmethod
    def _parse_action(cls, action: TemplateActionSchema) -> NotificationActionTemplate:
        return NotificationActionTemplate(
            type=action.type,
            text=action.text,
            viewname=action.viewname,
            viewname_kwargs=MappingProxyType(action.viewname_kwargs),
            redirect=action.redirect,
            redirect_kwargs=MappingProxyType(action.redirect_kwargs),
            style=action.style,
            next_template=action.next_template,
            new_related_object_id=action.new_related_object_id,
        )
