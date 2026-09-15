from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import validate_avatar_size

ALLOWED_AVATAR_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']


class User(AbstractUser):
    DM_EVERYONE = 'everyone'
    DM_FOLLOWERS = 'followers'
    DM_NOBODY = 'nobody'
    DM_PRIVACY_CHOICES = [
        (DM_EVERYONE, 'Everyone (message requests for non-followers)'),
        (DM_FOLLOWERS, 'Only people I follow'),
        (DM_NOBODY, 'No one'),
    ]

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
    dm_privacy = models.CharField(
        max_length=10, choices=DM_PRIVACY_CHOICES, default=DM_EVERYONE
    )

    def get_display_name(self):
        return self.display_name or self.username

    def __str__(self):
        return self.username
