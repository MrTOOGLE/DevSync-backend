from typing import Literal, Optional

from django.apps import apps
from pydantic import BaseModel, field_validator, Field


class TemplateActionSchema(BaseModel):
    type: Literal['request', 'anchor']
    text: str = Field(max_length=64)
    style: Literal['primary', 'secondary', 'danger']
    viewname: Optional[str] = None
    viewname_kwargs: dict[str, str] = {}
    redirect: Optional[str] = None
    redirect_kwargs: dict[str, str] = {}
    next_template: Optional[str] = None
    new_related_object_id: Optional[str] = None


class TemplateSchema(BaseModel):
    title: str = Field(max_length=128)
    message: str = Field(max_length=256)
    content_type: str
    actions: list[TemplateActionSchema] = []
    footnote: Optional[str] = Field(max_length=256, default=None)

    @field_validator('content_type')
    def validate_content_type_model(cls, v: str) -> str:
        if v.count(":") != 1:
            raise ValueError(
                "Field <content_type> must have comma-separated values: app:modelname (For example, users:user)"
            )
        app_label, model_name = v.split(':')

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise ValueError(f"Model <'{app_label}.{model_name}'> is not found.")

        return v
