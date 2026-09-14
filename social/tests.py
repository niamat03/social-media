from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from posts.models import Post

from .models import Follow, Notification

User = get_user_model()


class FollowConstraintTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass12345')
        self.bob = User.objects.create_user(username='bob', password='pass12345')

    def test_duplicate_follow_is_rejected(self):
        Follow.objects.create(follower=self.alice, following=self.bob)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.alice, following=self.bob)

    def test_self_follow_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.alice, following=self.alice)


class FollowToggleViewTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass12345')
        self.bob = User.objects.create_user(username='bob', password='pass12345')

    def test_follow_then_unfollow_toggles(self):
        self.client.login(username='alice', password='pass12345')
        url = reverse('social:follow_toggle', args=['bob'])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['following'])
        self.assertTrue(Follow.objects.filter(follower=self.alice, following=self.bob).exists())

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['following'])
        self.assertFalse(Follow.objects.filter(follower=self.alice, following=self.bob).exists())

    def test_cannot_follow_self_via_view(self):
        self.client.login(username='alice', password='pass12345')
        response = self.client.post(reverse('social:follow_toggle', args=['alice']))
        self.assertEqual(response.status_code, 400)

    def test_anonymous_user_cannot_follow(self):
        response = self.client.post(reverse('social:follow_toggle', args=['bob']))
        self.assertEqual(response.status_code, 302)  # redirected to login

    def test_following_creates_notification(self):
        self.client.login(username='alice', password='pass12345')
        self.client.post(reverse('social:follow_toggle', args=['bob']))
        self.assertTrue(
            Notification.objects.filter(recipient=self.bob, actor=self.alice, verb=Notification.FOLLOW).exists()
        )

    def test_unfollowing_does_not_duplicate_notification(self):
        self.client.login(username='alice', password='pass12345')
        url = reverse('social:follow_toggle', args=['bob'])
        self.client.post(url)  # follow
        self.client.post(url)  # unfollow
        self.assertEqual(
            Notification.objects.filter(recipient=self.bob, actor=self.alice, verb=Notification.FOLLOW).count(), 1
        )


class NotificationViewTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass12345')
        self.bob = User.objects.create_user(username='bob', password='pass12345')
        self.post = Post.objects.create(author=self.bob, content='hello')

    def test_liking_a_post_notifies_the_author(self):
        self.client.login(username='alice', password='pass12345')
        self.client.post(reverse('posts:like_toggle', args=[self.post.id]))
        self.assertTrue(
            Notification.objects.filter(recipient=self.bob, actor=self.alice, verb=Notification.LIKE).exists()
        )

    def test_commenting_notifies_the_author(self):
        self.client.login(username='alice', password='pass12345')
        self.client.post(reverse('posts:add_comment', args=[self.post.id]), {'content': 'nice!'})
        self.assertTrue(
            Notification.objects.filter(recipient=self.bob, actor=self.alice, verb=Notification.COMMENT).exists()
        )

    def test_liking_own_post_does_not_notify_self(self):
        self.client.login(username='bob', password='pass12345')
        self.client.post(reverse('posts:like_toggle', args=[self.post.id]))
        self.assertFalse(Notification.objects.filter(recipient=self.bob, actor=self.bob).exists())

    def test_viewing_notifications_marks_them_read(self):
        Notification.objects.create(recipient=self.bob, actor=self.alice, verb=Notification.FOLLOW)
        self.client.login(username='bob', password='pass12345')
        response = self.client.get(reverse('social:notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Notification.objects.filter(recipient=self.bob, is_read=False).exists())
