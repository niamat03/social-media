from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.validators import FileExtensionValidator
from django.db import models

from .validators import validate_image_size

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts'
    )
    content = models.TextField(max_length=2000)
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Geospatial: attached only when the author explicitly shares a location
    # for this specific post. Never derived from a persisted user location.
    location = gis_models.PointField(geography=True, srid=4326, null=True, blank=True)
    location_name = models.CharField(max_length=150, blank=True)
    city = models.CharField(max_length=100, blank=True)

    hashtags = models.ManyToManyField('Hashtag', related_name='posts', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return f'Post({self.author_id}, {self.id})'

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f'#{self.name}'


class SavedPost(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_saved_post_per_user')
        ]

    def __str__(self):
        return f'SavedPost({self.user_id} -> {self.post_id})'


class Report(models.Model):
    SPAM = 'spam'
    HARASSMENT = 'harassment'
    INAPPROPRIATE = 'inappropriate'
    OTHER = 'other'
    REASON_CHOICES = [
        (SPAM, 'Spam'),
        (HARASSMENT, 'Harassment or bullying'),
        (INAPPROPRIATE, 'Inappropriate content'),
        (OTHER, 'Other'),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_filed'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report({self.reporter_id} on post {self.post_id}: {self.reason})'


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes'
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_like_per_user_post')
        ]

    def __str__(self):
        return f'Like({self.user_id} -> {self.post_id})'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments'
    )
    content = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['post', 'created_at'])]

    def __str__(self):
        return f'Comment({self.author_id} on {self.post_id})'
