from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class NotificationAction:
    type: Literal['request', 'anchor']
    text: str
    payload: dict[str, Any]
    style: Literal['primary', 'secondary', 'danger']
