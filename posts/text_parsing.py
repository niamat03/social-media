import re

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import escape

from .models import Hashtag

HASHTAG_PATTERN = re.compile(r'#(\w+)')
MENTION_PATTERN = re.compile(r'@(\w+)')


def extract_hashtag_names(content):
    return {match.lower() for match in HASHTAG_PATTERN.findall(content)}


def extract_mentioned_usernames(content):
    return {match for match in MENTION_PATTERN.findall(content)}


def sync_hashtags(post):
    names = extract_hashtag_names(post.content)
    hashtags = [Hashtag.objects.get_or_create(name=name)[0] for name in names]
    post.hashtags.set(hashtags)


def get_mentioned_users(content, exclude_user=None):
    User = get_user_model()
    usernames = extract_mentioned_usernames(content)
    if not usernames:
        return User.objects.none()
    queryset = User.objects.filter(username__in=usernames)
    if exclude_user is not None:
        queryset = queryset.exclude(id=exclude_user.id)
    return queryset


def linkify_content(content):
    """Escape post content, then wrap #hashtags and @mentions with links.

    Escaping happens first so the raw text can never inject markup; the
    hashtag/mention substitution only ever adds well-formed anchors around
    already-safe text.
    """
    safe = escape(content)

    def hashtag_repl(match):
        word = match.group(1)
        url = reverse('posts:hashtag', args=[word.lower()])
        return f'<a class="content-tag" href="{url}">#{word}</a>'

    def mention_repl(match):
        word = match.group(1)
        url = reverse('accounts:profile', args=[word])
        return f'<a class="content-tag" href="{url}">@{word}</a>'

    safe = HASHTAG_PATTERN.sub(hashtag_repl, safe)
    safe = MENTION_PATTERN.sub(mention_repl, safe)
    return safe
