from django.conf import settings
from django.db import models


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_set'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow_pair'),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F('following')), name='no_self_follow'
            ),
        ]

    def __str__(self):
        return f'Follow({self.follower_id} -> {self.following_id})'


class Block(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocking_set'
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blocked_by_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['blocker', 'blocked'], name='unique_block_pair'),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F('blocked')), name='no_self_block'
            ),
        ]

    def __str__(self):
        return f'Block({self.blocker_id} -> {self.blocked_id})'


class Notification(models.Model):
    LIKE = 'like'
    COMMENT = 'comment'
    FOLLOW = 'follow'
    MENTION = 'mention'
    VERB_CHOICES = [
        (LIKE, 'liked your post'),
        (COMMENT, 'commented on your post'),
        (FOLLOW, 'started following you'),
        (MENTION, 'mentioned you in a post'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+'
    )
    verb = models.CharField(max_length=10, choices=VERB_CHOICES)
    post = models.ForeignKey('posts.Post', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', 'is_read'])]

    def __str__(self):
        return f'Notification({self.actor_id} -> {self.recipient_id}: {self.verb})'
