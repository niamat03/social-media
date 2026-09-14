from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE_MB = 5


def validate_image_size(file):
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f'Image must be smaller than {MAX_UPLOAD_SIZE_MB}MB.')
