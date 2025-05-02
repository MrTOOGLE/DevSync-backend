from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional, ClassVar

from notifications.services.schemes import ActionType, ActionStyle, ActionName, HttpMethod


@dataclass(frozen=True)
class NotificationActionTemplate:
    type: ActionType
    text: str
    style: ActionStyle
    viewname: Optional[str] = None
    viewname_kwargs: MappingProxyType[str, str] = MappingProxyType({})
    redirect: Optional[str] = None
    redirect_kwargs: MappingProxyType[str, str] = MappingProxyType({})
    method: Optional[HttpMethod] = None
    next_template: Optional[str] = None


@dataclass(frozen=True)
class NotificationTemplate:
    UPDATE_FIELDS: ClassVar[list[str]] = ['title', 'message', 'footnote']

    title: str
    message: str
    actions: MappingProxyType[ActionName, NotificationActionTemplate] = MappingProxyType({})
    footnote: Optional[str] = None

    def __post_init__(self):
        for field_name in self.UPDATE_FIELDS:
            if not (hasattr(self.__class__, field_name) or hasattr(self, field_name)):
                raise ValueError(f'Field {field_name} is not declared.')
