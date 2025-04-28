from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Optional, ClassVar

from config.utils.lazy import LazyContentType


@dataclass(frozen=True)
class NotificationActionTemplate:
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
    content_type_app: str
    content_type_model: str
    actions: tuple[NotificationActionTemplate, ...] = field(default_factory=tuple)
    footnote: Optional[str] = None
    _lazy_content_type: LazyContentType = field(init=False, repr=False)

    def __post_init__(self):
        for field_name in self.MAPPED_FIELDS:
            if not (hasattr(self.__class__, field_name) or hasattr(self, field_name)):
                raise ValueError(f'Field {field_name} is not declared.')

        object.__setattr__(
            self,
            '_lazy_content_type',
            LazyContentType(self.content_type_app, self.content_type_model),
        )

    @property
    def content_type(self):
        return self._lazy_content_type()
