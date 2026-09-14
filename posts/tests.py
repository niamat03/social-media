import io
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .forms import PostForm
from .models import Comment, Hashtag, Like, Post, Report, SavedPost
from .text_parsing import extract_hashtag_names, extract_mentioned_usernames, sync_hashtags
from .validators import validate_image_size

User = get_user_model()


def make_test_image(name='test.png'):
    buffer = io.BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type='image/png')


class LikeConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass12345')
        self.post = Post.objects.create(author=self.user, content='hello')

    def test_duplicate_like_is_rejected_by_database(self):
        Like.objects.create(user=self.user, post=self.post)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Like.objects.create(user=self.user, post=self.post)


class PostAuthorizationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass12345')
        self.other = User.objects.create_user(username='other', password='pass12345')
        self.post = Post.objects.create(author=self.owner, content='mine')

    def test_non_owner_cannot_delete_post(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.post(reverse('posts:delete', args=[self.post.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())

    def test_owner_can_delete_post(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.post(reverse('posts:delete', args=[self.post.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())


class PostEditTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner2', password='pass12345')
        self.other = User.objects.create_user(username='other2', password='pass12345')
        self.post = Post.objects.create(author=self.owner, content='original')

    def test_owner_can_edit_post(self):
        self.client.login(username='owner2', password='pass12345')
        response = self.client.post(
            reverse('posts:edit', args=[self.post.id]), {'content': 'updated content'}
        )
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'updated content')

    def test_non_owner_cannot_edit_post(self):
        self.client.login(username='other2', password='pass12345')
        response = self.client.post(
            reverse('posts:edit', args=[self.post.id]), {'content': 'hacked'}
        )
        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, 'original')


class CommentTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='author3', password='pass12345')
        self.commenter = User.objects.create_user(username='commenter3', password='pass12345')
        self.post = Post.objects.create(author=self.author, content='post')

    def test_authenticated_user_can_add_comment(self):
        self.client.login(username='commenter3', password='pass12345')
        response = self.client.post(
            reverse('posts:add_comment', args=[self.post.id]), {'content': 'Nice post!'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.post.comments.count(), 1)

    def test_non_author_cannot_delete_comment(self):
        comment = Comment.objects.create(post=self.post, author=self.commenter, content='hi')
        self.client.login(username='author3', password='pass12345')
        response = self.client.post(reverse('posts:delete_comment', args=[comment.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(id=comment.id).exists())

    def test_author_can_delete_own_comment(self):
        comment = Comment.objects.create(post=self.post, author=self.commenter, content='hi')
        self.client.login(username='commenter3', password='pass12345')
        response = self.client.post(reverse('posts:delete_comment', args=[comment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_author_can_edit_own_comment(self):
        comment = Comment.objects.create(post=self.post, author=self.commenter, content='original')
        self.client.login(username='commenter3', password='pass12345')
        response = self.client.post(
            reverse('posts:edit_comment', args=[comment.id]), {'content': 'edited'}
        )
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'edited')

    def test_non_author_cannot_edit_comment(self):
        comment = Comment.objects.create(post=self.post, author=self.commenter, content='original')
        self.client.login(username='author3', password='pass12345')
        response = self.client.post(
            reverse('posts:edit_comment', args=[comment.id]), {'content': 'hacked'}
        )
        self.assertEqual(response.status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'original')


class ImageValidationTests(TestCase):
    def test_oversized_image_is_rejected_by_validator(self):
        fake_file = SimpleNamespace(size=6 * 1024 * 1024)  # 6MB, over the 5MB limit
        with self.assertRaises(ValidationError):
            validate_image_size(fake_file)

    def test_image_within_limit_passes_validator(self):
        fake_file = SimpleNamespace(size=1 * 1024 * 1024)
        validate_image_size(fake_file)  # should not raise

    def test_invalid_file_type_is_rejected_by_form(self):
        bad_file = SimpleUploadedFile('notes.txt', b'not an image', content_type='text/plain')
        form = PostForm(data={'content': 'hi'}, files={'image': bad_file})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_valid_image_is_accepted_by_form(self):
        form = PostForm(data={'content': 'hi'}, files={'image': make_test_image()})
        self.assertTrue(form.is_valid(), form.errors)


class SavedPostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='saver', password='pass12345')
        self.author = User.objects.create_user(username='poster', password='pass12345')
        self.post = Post.objects.create(author=self.author, content='save me')

    def test_save_then_unsave_toggles(self):
        self.client.login(username='saver', password='pass12345')
        url = reverse('posts:save_toggle', args=[self.post.id])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertTrue(SavedPost.objects.filter(user=self.user, post=self.post).exists())

        response = self.client.post(url)
        self.assertFalse(response.json()['saved'])
        self.assertFalse(SavedPost.objects.filter(user=self.user, post=self.post).exists())

    def test_duplicate_save_is_rejected_by_database(self):
        SavedPost.objects.create(user=self.user, post=self.post)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SavedPost.objects.create(user=self.user, post=self.post)


class ReportTests(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(username='reporter', password='pass12345')
        self.author = User.objects.create_user(username='reported_author', password='pass12345')
        self.post = Post.objects.create(author=self.author, content='sketchy post')

    def test_authenticated_user_can_report_post(self):
        self.client.login(username='reporter', password='pass12345')
        response = self.client.post(
            reverse('posts:report', args=[self.post.id]), {'reason': 'spam', 'details': 'looks fake'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Report.objects.filter(post=self.post, reporter=self.reporter, reason='spam').exists())

    def test_cannot_report_own_post(self):
        self.client.login(username='reported_author', password='pass12345')
        response = self.client.post(reverse('posts:report', args=[self.post.id]), {'reason': 'spam'})
        self.assertEqual(response.status_code, 400)

    def test_invalid_reason_is_rejected(self):
        self.client.login(username='reporter', password='pass12345')
        response = self.client.post(reverse('posts:report', args=[self.post.id]), {'reason': 'not-a-reason'})
        self.assertEqual(response.status_code, 400)


class HashtagMentionParsingTests(TestCase):
    def test_extract_hashtag_names_lowercases_and_dedupes(self):
        names = extract_hashtag_names('Loving #Morocco and #morocco today #Travel')
        self.assertEqual(names, {'morocco', 'travel'})

    def test_extract_mentioned_usernames(self):
        usernames = extract_mentioned_usernames('Hey @alice and @bob, check this out')
        self.assertEqual(usernames, {'alice', 'bob'})

    def test_sync_hashtags_creates_and_links(self):
        user = User.objects.create_user(username='tagger', password='pass12345')
        post = Post.objects.create(author=user, content='Beautiful day in #Tangier')
        sync_hashtags(post)
        self.assertTrue(Hashtag.objects.filter(name='tangier').exists())
        self.assertIn(post, Hashtag.objects.get(name='tangier').posts.all())

    def test_hashtag_view_lists_matching_posts(self):
        user = User.objects.create_user(username='tagger2', password='pass12345')
        post = Post.objects.create(author=user, content='Sunset in #Tangier again')
        sync_hashtags(post)
        response = self.client.get(reverse('posts:hashtag', args=['tangier']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sunset in')
