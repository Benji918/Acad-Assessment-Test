import re
import bleach
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_no_special_chars(value):
    '''Validates that a string contains only alphanumeric characters and basic punctuation.'''
    if not re.match(r'^[a-zA-Z0-9\s\.,;:!?\-]+$', value):
        raise ValidationError(
            _('Text contains invalid characters. Only letters, numbers, and basic punctuation allowed.')
        )

def sanitize_html_input(text):
    '''Sanitizes HTML input to prevent XSS attacks.'''
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
    allowed_attributes = {}
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def validate_answer_length(value, max_length=5000):
    '''Validates answer text length.'''
    if len(value) > max_length:
        raise ValidationError(
            _(f'Answer text cannot exceed {max_length} characters.')
        )