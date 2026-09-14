from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import validate_avatar_size

ALLOWED_AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']


class User(AbstractUser):
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.CharField(max_length=280, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_AVATAR_EXTENSIONS),
            validate_avatar_size,
        ],
    )

    def get_display_name(self):
        return self.display_name or self.username

    def __str__(self):
        return self.username
