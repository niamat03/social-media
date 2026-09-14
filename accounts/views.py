from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render

from posts.models import Post
from posts.views import annotate_post_extras
from social.models import Block, Follow

from .forms import ProfileEditForm, RegisterForm
from .models import User


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'


class AccountLogoutView(LogoutView):
    pass


def register_view(request):
    if request.user.is_authenticated:
        return redirect('posts:feed')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('posts:feed')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = annotate_post_extras(
        Post.objects.filter(author=profile_user).select_related('author').order_by('-created_at'),
        request.user,
    )

    is_following = False
    is_blocked = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user, following=profile_user
        ).exists()
        is_blocked = Block.objects.filter(blocker=request.user, blocked=profile_user).exists()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'followers_count': Follow.objects.filter(following=profile_user).count(),
        'following_count': Follow.objects.filter(follower=profile_user).count(),
        'posts_count': posts.count(),
        'is_following': is_following,
        'is_blocked': is_blocked,
        'is_own_profile': request.user.is_authenticated and request.user == profile_user,
    }
    return render(request, 'accounts/profile.html', context)


def followers_view(request, username):
    from social.views import _annotate_following

    profile_user = get_object_or_404(User, username=username)
    follower_ids = Follow.objects.filter(following=profile_user).values_list('follower_id', flat=True)
    users = _annotate_following(User.objects.filter(id__in=follower_ids), request.user)
    return render(request, 'accounts/user_list.html', {
        'profile_user': profile_user,
        'users': users,
        'list_title': 'Followers',
    })


def following_view(request, username):
    from social.views import _annotate_following

    profile_user = get_object_or_404(User, username=username)
    following_ids = Follow.objects.filter(follower=profile_user).values_list('following_id', flat=True)
    users = _annotate_following(User.objects.filter(id__in=following_ids), request.user)
    return render(request, 'accounts/user_list.html', {
        'profile_user': profile_user,
        'users': users,
        'list_title': 'Following',
    })


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})
