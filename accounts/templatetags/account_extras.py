import urllib.parse

from django import template

register = template.Library()

# Geometric, non-photographic identicons keyed by username — deliberately
# abstract so no generated avatar could be mistaken for a real person's photo.
AVATAR_BASE_URL = 'https://api.dicebear.com/9.x/identicon/svg'


@register.filter
def avatar_url(user):
    if getattr(user, 'avatar', None):
        return user.avatar.url
    seed = urllib.parse.quote(user.username)
    return f'{AVATAR_BASE_URL}?seed={seed}&backgroundType=gradientLinear'
