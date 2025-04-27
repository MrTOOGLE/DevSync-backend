from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Optional, ClassVar

from django.contrib.contenttypes.models import ContentType


@dataclass(frozen=True)
class NotificationTemplateAction:
    type: Literal['request', 'anchor']
    text: str
    style: Literal['primary', 'secondary', 'danger']
    viewname: Optional[str] = None
    viewname_kwargs: MappingProxyType[str, str] = MappingProxyType({})
    redirect: Optional[str] = None
    redirect_kwargs: MappingProxyType[str, str] = MappingProxyType({})
    next_template: Optional[str] = None
    new_related_object_id: Optional[str] = None


@dataclass(frozen=True)
class NotificationTemplate:
    MAPPED_FIELDS: ClassVar[list[str]] = ['title', 'message', 'content_type', 'footnote']

    title: str
    message: str
    content_type: ContentType
    actions: tuple[NotificationTemplateAction, ...] = ()
    footnote: Optional[str] = None

    def __post_init__(self):
        for field in self.MAPPED_FIELDS:
            if not hasattr(self, field):
                raise ValueError(f'Field {field} has is not declared.')
