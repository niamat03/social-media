from django.db.models import Q

from .models import Block


def is_blocked_either_way(user_a, user_b):
    if not user_a.is_authenticated:
        return False
    return Block.objects.filter(
        Q(blocker=user_a, blocked=user_b) | Q(blocker=user_b, blocked=user_a)
    ).exists()


def blocked_user_ids_either_way(user):
    """IDs of users who should be hidden from `user`'s feeds/search: whoever
    they blocked, and whoever blocked them."""
    if not user.is_authenticated:
        return set()
    blocked = Block.objects.filter(blocker=user).values_list('blocked_id', flat=True)
    blocked_by = Block.objects.filter(blocked=user).values_list('blocker_id', flat=True)
    return set(blocked) | set(blocked_by)
