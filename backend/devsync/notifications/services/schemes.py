from typing import Literal, Optional, TypeAlias

from pydantic import BaseModel, Field

ActionType: TypeAlias = Literal['request', 'anchor']
ActionName: TypeAlias = Literal['accept', 'reject', 'ok', 'go']
ActionStyle: TypeAlias = Literal['primary', 'secondary', 'danger']

class TemplateActionSchema(BaseModel):
    type: ActionType
    text: str = Field(max_length=64)
    style: ActionStyle
    viewname: Optional[str] = None
    viewname_kwargs: dict[str, str] = {}
    redirect: Optional[str] = None
    redirect_kwargs: dict[str, str] = {}
    next_template: Optional[str] = None


class TemplateSchema(BaseModel):
    title: str = Field(max_length=128)
    message: str = Field(max_length=256)
    actions: dict[ActionName, TemplateActionSchema] = Field(default_factory=dict)
    footnote: Optional[str] = Field(max_length=256, default=None)
