from django.core.exceptions import ValidationError
import re

def validate_hex_color(value):
    pattern = r'^#[A-Fa-f0-9]{6}'
    if not re.match(pattern, value):
        raise ValidationError(f'Invalid HEX color format. Got: {value}, Expected: #RRGGBB')
