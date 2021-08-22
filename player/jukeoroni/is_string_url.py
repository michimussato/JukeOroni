from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


def is_string_url(url_string):
    validate_url = URLValidator()
    try:
        validate_url(url_string)
    except ValidationError:
        return False
    return True
