import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from django.urls import reverse
from rest_framework.exceptions import ParseError

from notifications.models import Notification
from notifications.services.actions import NotificationAction


@dataclass(frozen=True)
class NotificationTemplateAction:
    type: Literal['only_request', 'only_redirect', 'both']
    text: str
    style: Literal['accept', 'reject', 'info', 'danger']
    viewname: str | None
    viewname_kwargs: MappingProxyType[str, str] | None
    redirect: str | None
    redirect_kwargs: MappingProxyType[str, str] | None
    to_template: str | None
    new_related_object_id: str | None


@dataclass(frozen=True)
class NotificationTemplate:
    title: str
    message: str
    content_type: ContentType
    actions: tuple[NotificationTemplateAction, ...]


templates_paths = {}
def register_templates(app: str, templates_path: str) -> None:
    templates_path = Path(static(templates_path)[1:])
    if not os.path.exists(templates_path) and not os.path.isdir(templates_path):
        raise FileNotFoundError(f"File with path <{templates_path}> does not exist.")
    templates_paths[app] = templates_path


class NotificationTemplatesBuilder:
    _templates: dict[str, NotificationTemplate] = {}

    @classmethod
    def get_templates(cls) -> MappingProxyType[str, NotificationTemplate]:
        if not cls._templates:
            cls._load_templates()
        return MappingProxyType(cls._templates)

    @classmethod
    def _load_templates(cls):
        for app, template_path in templates_paths.items():
            with open(template_path, 'r') as file:
                templates = json.loads(file.read())
            if templates:
                for name, template in templates.items():
                    cls._templates[name] = cls._parse_template(template, name)

    @classmethod
    def _parse_template(cls, template_dict: dict, template_name: str) -> NotificationTemplate:
        try:
            title = template_dict.get('title')
            message = template_dict.get('message')
            content_type_app, content_type_name = template_dict.get('content_type').split(':')
            content_type = ContentType.objects.get(app_label=content_type_app, model=content_type_name)
            actions = template_dict.get('actions', [])
            actions = cls._parse_actions(actions, template_name)
        except (KeyError, ValueError):
            raise ParseError(f"Cant parse notification template with name <{template_name}>. Check your fields.")
        except ContentType.DoesNotExist:
            raise ParseError(f"Cant parse notification template with name <{template_name}>. Unknown content type.")
        return NotificationTemplate(
            title=title,
            message=message,
            content_type=content_type,
            actions=tuple(actions)
        )

    @staticmethod
    def _parse_actions(actions: list[dict], template_name: str) -> list[NotificationTemplateAction]:
        parsed_actions = []
        for action in actions:
            try:
                action_type = action.get('type')
                text = action.get('text', 'undefined')
                viewname = action.get('viewname', None)
                viewname_kwargs = action.get('viewname_kwargs', {})
                redirect = action.get('redirect', None)
                redirect_kwargs = action.get('redirect_kwargs', {})
                style = action.get('style')
                to_template = action.get('to_template', None)
                new_related_object_id = action.get('new_related_object_id', None)
            except KeyError:
                raise ParseError(f"Cant parse notification action with name <{template_name}>")
            parsed_actions.append(
                NotificationTemplateAction(
                    type=action_type,
                    text=text,
                    viewname=viewname,
                    viewname_kwargs=MappingProxyType(viewname_kwargs),
                    redirect=redirect,
                    redirect_kwargs=MappingProxyType(redirect_kwargs),
                    style=style,
                    to_template=to_template,
                    new_related_object_id=new_related_object_id
                )
            )
        return parsed_actions


class ActionBuilder:
    _built_actions: dict[str, list[NotificationAction]] = {}

    def __init__(self, template: NotificationTemplate, notification: Notification):
        self._template = template
        self._notification = notification

    def build(self) -> list[NotificationAction]:

        notification_actions = []
        for action in self._template.actions:
            kwargs = {}
            for key, value in action.viewname_kwargs.items():
                value = value.format(object=self._notification.content_object)
                if value.isdigit():
                    value = int(value)
                kwargs[key] = value
            url = reverse(action.viewname, kwargs=kwargs)
            payload = {'url': url}
            if action.to_template:
                payload['to_template'] = action.to_template
            if action.new_related_object_id:
                payload['new_related_object_id'] = action.new_related_object_id
            notification_actions.append(
                NotificationAction(
                    type=action.type,
                    text=action.text,
                    payload=payload,
                    style=action.style,
                )
            )
        return notification_actions
