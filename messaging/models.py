from django.conf import settings
from django.db import models


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def last_message(self):
        return self.messages.order_by('-created_at').first()

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
