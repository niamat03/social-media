from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from config.throttle import rate_limit
from social.block_utils import blocked_user_ids_either_way
from social.models import Block, Follow, Notification

from .forms import CommentForm, PostForm
from .models import Comment, Hashtag, Like, Post, Report, SavedPost
from .text_parsing import get_mentioned_users, sync_hashtags

User = get_user_model()


def _annotate_liked(queryset, user):
    if user.is_authenticated:
        liked_subquery = Like.objects.filter(post=OuterRef('pk'), user=user)
        return queryset.annotate(liked_by_user=Exists(liked_subquery))
    return queryset.annotate(liked_by_user=Value(False, output_field=BooleanField()))


def _annotate_saved(queryset, user):
    if user.is_authenticated:
        saved_subquery = SavedPost.objects.filter(post=OuterRef('pk'), user=user)
        return queryset.annotate(saved_by_user=Exists(saved_subquery))
    return queryset.annotate(saved_by_user=Value(False, output_field=BooleanField()))


def _annotate_author_blocked(queryset, user):
    if user.is_authenticated:
        blocked_subquery = Block.objects.filter(blocker=user, blocked=OuterRef('author_id'))
        return queryset.annotate(author_is_blocked=Exists(blocked_subquery))
    return queryset.annotate(author_is_blocked=Value(False, output_field=BooleanField()))


def annotate_post_extras(queryset, user):
    queryset = _annotate_liked(queryset, user)
    queryset = _annotate_saved(queryset, user)
    queryset = _annotate_author_blocked(queryset, user)
    return queryset


def _handle_post_side_effects(post, author):
    sync_hashtags(post)
    for mentioned_user in get_mentioned_users(post.content, exclude_user=author):
        Notification.objects.create(
            recipient=mentioned_user, actor=author, verb=Notification.MENTION, post=post
        )


@login_required
def feed_view(request):
    tab = request.GET.get('tab', 'following')

    following_ids = list(
        Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    )
    hidden_ids = blocked_user_ids_either_way(request.user)

    posts = Post.objects.select_related('author').exclude(author_id__in=hidden_ids)

    if tab == 'following':
        posts = posts.filter(author_id__in=following_ids + [request.user.id])

    posts = annotate_post_extras(posts, request.user).order_by('-created_at')

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            _handle_post_side_effects(post, request.user)
            return redirect('posts:feed')
    else:
        form = PostForm()

    suggested_users = (
        User.objects.exclude(id__in=following_ids + [request.user.id] + list(hidden_ids))
        .annotate(followers_count=Count('followers_set'), is_following=Value(False, output_field=BooleanField()))
        .order_by('-followers_count')[:5]
    )

    return render(request, 'posts/feed.html', {
        'form': form,
        'page_obj': page_obj,
        'tab': tab,
        'suggested_users': suggested_users,
    })


def post_detail_view(request, pk):
    posts = annotate_post_extras(Post.objects.select_related('author'), request.user)
    post = get_object_or_404(posts, pk=pk)
    comments_qs = post.comments.select_related('author').all()
    comments_paginator = Paginator(comments_qs, 20)
    comments_page = comments_paginator.get_page(request.GET.get('comment_page'))
    comment_form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments_page': comments_page,
        'comment_form': comment_form,
    })


def hashtag_view(request, name):
    hashtag = get_object_or_404(Hashtag, name=name.lower())
    posts = annotate_post_extras(
        hashtag.posts.select_related('author').order_by('-created_at'), request.user
    )
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'posts/hashtag.html', {'hashtag': hashtag, 'page_obj': page_obj})


@login_required
def saved_posts_view(request):
    posts = (
        Post.objects.filter(saved_by__user=request.user)
        .select_related('author')
        .order_by('-saved_by__created_at')
    )
    posts = annotate_post_extras(posts, request.user)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'posts/saved.html', {'page_obj': page_obj})


@login_required
def delete_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author_id != request.user.id:
        raise PermissionDenied('You cannot delete another user\'s post.')
    if request.method == 'POST':
        post.delete()
        return redirect('posts:feed')
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def edit_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author_id != request.user.id:
        raise PermissionDenied('You cannot edit another user\'s post.')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            _handle_post_side_effects(post, request.user)
            return redirect('posts:detail', pk=post.id)
    else:
        initial = {}
        if post.location:
            initial = {'latitude': post.location.y, 'longitude': post.location.x}
        form = PostForm(instance=post, initial=initial)

    return render(request, 'posts/post_edit.html', {'form': form, 'post': post})


@login_required
@rate_limit('like', limit=60, window=60)
def like_toggle_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    like = Like.objects.filter(post=post, user=request.user).first()
    if like:
        like.delete()
        liked = False
    else:
        Like.objects.create(post=post, user=request.user)
        liked = True
        if post.author_id != request.user.id:
            Notification.objects.create(recipient=post.author, actor=request.user, verb='like', post=post)

    return JsonResponse({'liked': liked, 'like_count': post.like_count})


@login_required
@rate_limit('save', limit=60, window=60)
def save_toggle_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    saved = SavedPost.objects.filter(post=post, user=request.user).first()
    if saved:
        saved.delete()
        is_saved = False
    else:
        SavedPost.objects.create(post=post, user=request.user)
        is_saved = True

    return JsonResponse({'saved': is_saved})


@login_required
@rate_limit('report', limit=10, window=60)
def report_post_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if post.author_id == request.user.id:
        return JsonResponse({'error': "You can't report your own post."}, status=400)

    reason = request.POST.get('reason', '')
    if reason not in dict(Report.REASON_CHOICES):
        return JsonResponse({'error': 'Invalid reason.'}, status=400)

    Report.objects.create(
        reporter=request.user,
        post=post,
        reason=reason,
        details=request.POST.get('details', '')[:500],
    )
    return JsonResponse({'reported': True})


@login_required
@rate_limit('comment', limit=30, window=60)
def add_comment_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    form = CommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)

    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()

    if post.author_id != request.user.id:
        Notification.objects.create(recipient=post.author, actor=request.user, verb='comment', post=post)

    return JsonResponse({
        'id': comment.id,
        'author': comment.author.get_display_name(),
        'author_username': comment.author.username,
        'content': comment.content,
        'created_at': comment.created_at.strftime('%b %d, %Y %H:%M'),
        'comment_count': post.comment_count,
    })


@login_required
def edit_comment_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author_id != request.user.id:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    form = CommentForm(request.POST, instance=comment)
    if not form.is_valid():
        return JsonResponse({'error': form.errors}, status=400)

    comment = form.save()
    return JsonResponse({'id': comment.id, 'content': comment.content})


@login_required
def delete_comment_view(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author_id != request.user.id:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    post = comment.post
    comment.delete()
    return JsonResponse({'comment_count': post.comment_count})
