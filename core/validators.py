import re
import bleach
from rest_framework import serializers
from email_validator import validate_email, EmailNotValidError, caching_resolver
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

def sanitize_email(email):
    """
    Validates email through multiple checks:
    1. Basic format validation
    2. Domain existence check
    3. Common disposable email domain check
    """

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise serializers.ValidationError("Invalid email format")

    # Split email into local and domain parts
    local_part, domain = email.rsplit('@', 1)

    # Check for common disposable email domains
    disposable_domains = {
        'tempmail.com', 'throwawaymail.com', 'mailinator.com',
        'temporary-mail.net', 'fake-email.com', 'example.com',
        'guerrillamail.com', '10minutemail.com', 'yopmail.com',
        'trashmail.com', 'temp-mail.org', 'sharklasers.com',
        'getairmail.com', 'maildrop.cc', 'dispostable.com'
    }

    if domain.lower() in disposable_domains:
        raise serializers.ValidationError({"email": "Disposable email addresses are not allowed"})


    try:
        resolver = caching_resolver(timeout=10)
        v = validate_email(email, dns_resolver=resolver, check_deliverability=True)
    except EmailNotValidError as e:
        raise serializers.ValidationError({"email": f"Invalid email domain: {e}"})


    return True