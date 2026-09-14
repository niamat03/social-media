from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE_MB = 2


def validate_avatar_size(file):
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f'Avatar must be smaller than {MAX_UPLOAD_SIZE_MB}MB.')
