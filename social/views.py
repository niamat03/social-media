from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from config.throttle import rate_limit
from posts.models import Post
from posts.views import annotate_post_extras

from .block_utils import blocked_user_ids_either_way
from .models import Block, Follow, Notification

User = get_user_model()


def _annotate_following(queryset, user):
    if user.is_authenticated:
        follow_subquery = Follow.objects.filter(follower=user, following=OuterRef('pk'))
        return queryset.annotate(is_following=Exists(follow_subquery))
    return queryset.annotate(is_following=Value(False, output_field=BooleanField()))


@login_required
@rate_limit('follow', limit=40, window=60)
def follow_toggle_view(request, username):
    target = get_object_or_404(User, username=username)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if target == request.user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)

    if Block.objects.filter(
        Q(blocker=request.user, blocked=target) | Q(blocker=target, blocked=request.user)
    ).exists():
        return JsonResponse({'error': 'You cannot follow this user.'}, status=403)

    follow = Follow.objects.filter(follower=request.user, following=target).first()
    if follow:
        follow.delete()
        following = False
    else:
        Follow.objects.create(follower=request.user, following=target)
        Notification.objects.create(recipient=target, actor=request.user, verb=Notification.FOLLOW)
        following = True

    return JsonResponse({
        'following': following,
        'followers_count': Follow.objects.filter(following=target).count(),
    })


@login_required
@rate_limit('block', limit=30, window=60)
def block_toggle_view(request, username):
    target = get_object_or_404(User, username=username)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if target == request.user:
        return JsonResponse({'error': 'Cannot block yourself'}, status=400)

    block = Block.objects.filter(blocker=request.user, blocked=target).first()
    if block:
        block.delete()
        blocked = False
    else:
        Block.objects.create(blocker=request.user, blocked=target)
        Follow.objects.filter(follower=request.user, following=target).delete()
        Follow.objects.filter(follower=target, following=request.user).delete()
        blocked = True

    return JsonResponse({'blocked': blocked})


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).select_related('actor', 'post')
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return render(request, 'social/notifications.html', {'notifications': notifications[:50]})


@login_required
def unread_notifications_count_api(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


def explore_view(request):
    since = timezone.now() - timedelta(days=7)
    hidden_ids = blocked_user_ids_either_way(request.user)

    trending_posts = annotate_post_extras(
        Post.objects.select_related('author')
        .exclude(author_id__in=hidden_ids)
        .annotate(recent_likes=Count('likes', filter=Q(likes__created_at__gte=since))),
        request.user,
    ).order_by('-recent_likes', '-created_at')[:20]

    popular_users = _annotate_following(
        User.objects.exclude(id=request.user.id if request.user.is_authenticated else None)
        .exclude(id__in=hidden_ids)
        .annotate(followers_count=Count('followers_set')),
        request.user,
    ).order_by('-followers_count')[:10]

    return render(request, 'social/explore.html', {
        'trending_posts': trending_posts,
        'popular_users': popular_users,
    })


def search_view(request):
    query = request.GET.get('q', '').strip()
    users = User.objects.none()
    posts = Post.objects.none()
    hidden_ids = blocked_user_ids_either_way(request.user)

    if query:
        users = _annotate_following(
            User.objects.filter(
                Q(username__icontains=query) | Q(display_name__icontains=query)
            ).exclude(id__in=hidden_ids),
            request.user,
        )[:20]
        posts = annotate_post_extras(
            Post.objects.select_related('author')
            .filter(content__icontains=query)
            .exclude(author_id__in=hidden_ids),
            request.user,
        ).order_by('-created_at')[:20]

    return render(request, 'social/search.html', {
        'query': query,
        'users': users,
        'posts': posts,
    })
