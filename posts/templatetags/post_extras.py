from django import template
from django.utils.safestring import mark_safe

from posts.text_parsing import linkify_content

register = template.Library()


@register.filter
def linkify(content):
    return mark_safe(linkify_content(content))
