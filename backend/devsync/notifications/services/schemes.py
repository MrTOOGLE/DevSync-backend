from typing import Literal, Optional, TypeAlias

from pydantic import BaseModel, Field, model_validator

ActionType: TypeAlias = Literal['request', 'anchor']
ActionName: TypeAlias = Literal['accept', 'reject', 'ok', 'go']
ActionStyle: TypeAlias = Literal['primary', 'secondary', 'danger']
HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

class TemplateActionSchema(BaseModel):
    type: ActionType
    text: str = Field(max_length=64)
    style: ActionStyle
    viewname: Optional[str] = None
    viewname_kwargs: dict[str, str] = {}
    method: Optional[HttpMethod] = None
    redirect: Optional[str] = None
    redirect_kwargs: dict[str, str] = {}
    next_template: Optional[str] = None

    @model_validator(mode="after")
    def validate_method_required_for_request(self):
        if self.type == 'request' and self.method is None:
            raise ValueError("Field 'method' is required when action type is 'request'")
        return self


class TemplateSchema(BaseModel):
    title: str = Field(max_length=128)
    message: str = Field(max_length=256)
    actions: dict[ActionName, TemplateActionSchema] = Field(default_factory=dict)
    footnote: Optional[str] = Field(max_length=256, default=None)
