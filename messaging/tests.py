from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Conversation, Message
from .views import get_or_create_conversation

User = get_user_model()


class MessagingTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass12345')
        self.bob = User.objects.create_user(username='bob', password='pass12345')

    def test_sending_message_creates_conversation(self):
        self.client.login(username='alice', password='pass12345')
        response = self.client.post(
            reverse('messaging:send', args=['bob']), {'content': 'Hey Bob!'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 1)
        message = Message.objects.first()
        self.assertEqual(message.sender, self.alice)
        self.assertEqual(message.content, 'Hey Bob!')

    def test_repeated_messages_reuse_same_conversation(self):
        self.client.login(username='alice', password='pass12345')
        self.client.post(reverse('messaging:send', args=['bob']), {'content': 'Hi'})
        self.client.login(username='bob', password='pass12345')
        self.client.post(reverse('messaging:send', args=['alice']), {'content': 'Hello back'})
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Conversation.objects.first().messages.count(), 2)

    def test_cannot_message_self(self):
        self.client.login(username='alice', password='pass12345')
        response = self.client.post(
            reverse('messaging:send', args=['alice']), {'content': 'hi me'}
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_message_is_rejected(self):
        self.client.login(username='alice', password='pass12345')
        response = self.client.post(reverse('messaging:send', args=['bob']), {'content': '  '})
        self.assertEqual(response.status_code, 400)

    def test_opening_conversation_marks_messages_read(self):
        conversation = get_or_create_conversation(self.alice, self.bob)
        Message.objects.create(conversation=conversation, sender=self.alice, content='Hi Bob')

        self.client.login(username='bob', password='pass12345')
        response = self.client.get(reverse('messaging:conversation', args=['alice']))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Message.objects.filter(conversation=conversation, is_read=False).exists()
        )

    def test_anonymous_user_cannot_access_inbox(self):
        response = self.client.get(reverse('messaging:inbox'))
        self.assertEqual(response.status_code, 302)
