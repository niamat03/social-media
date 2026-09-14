from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationLoginTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SuperSecret123!',
            'password2': 'SuperSecret123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

        feed_response = self.client.get(reverse('posts:feed'))
        self.assertEqual(feed_response.status_code, 200)

    def test_login_required_redirects_anonymous_user(self):
        response = self.client.get(reverse('posts:feed'))
        self.assertEqual(response.status_code, 302)

    def test_invalid_login_does_not_authenticate(self):
        User.objects.create_user(username='alice', password='pass12345')
        response = self.client.post(reverse('accounts:login'), {
            'username': 'alice',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 200)  # re-renders form with errors
        feed_response = self.client.get(reverse('posts:feed'))
        self.assertEqual(feed_response.status_code, 302)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pass12345')
        self.bob = User.objects.create_user(username='bob', password='pass12345')

    def test_profile_shows_follow_button_for_other_user(self):
        self.client.login(username='bob', password='pass12345')
        response = self.client.get(reverse('accounts:profile', args=['alice']))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_own_profile'])
        self.assertFalse(response.context['is_following'])

    def test_edit_profile_updates_fields(self):
        self.client.login(username='alice', password='pass12345')
        response = self.client.post(reverse('accounts:edit_profile'), {
            'display_name': 'Alice A.',
            'bio': 'Hello world',
        })
        self.assertEqual(response.status_code, 302)
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.display_name, 'Alice A.')
        self.assertEqual(self.alice.bio, 'Hello world')
