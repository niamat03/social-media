from django.conf import settings
from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    # A conversation started by someone the recipient doesn't follow is a
    # "message request": it stays out of the recipient's primary inbox and
    # `accepted` is False until they accept it (or reply, which auto-accepts).
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='initiated_conversations',
    )
    accepted = models.BooleanField(default=True)

    def other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def is_request_for(self, user):
        """Whether this conversation sits in `user`'s message requests (as
        opposed to their primary inbox)."""
        return not self.accepted and self.initiator_id != user.id

    def __str__(self):
        return f'Conversation({self.id})'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    content = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['conversation', 'created_at'])]

    def __str__(self):
        return f'Message({self.sender_id} in {self.conversation_id})'
