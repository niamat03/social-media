from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from config.throttle import rate_limit
from social.block_utils import is_blocked_either_way
from social.models import Follow

from .models import Conversation, Message

User = get_user_model()


def find_conversation(user_a, user_b):
    # Chaining two .filter(participants=...) calls on the same M2M produces two
    # separate joins; annotating Count('participants') afterwards double-counts
    # rows from that join multiplication, so the exact-pair check is done in
    # Python instead of via a single annotated queryset.
    candidates = Conversation.objects.filter(participants=user_a).filter(participants=user_b)
    for candidate in candidates:
        if candidate.participants.count() == 2:
            return candidate
    return None


def can_message(sender, recipient):
    """Whether `sender` is allowed to start a new conversation with
    `recipient`. Returns (allowed, reason)."""
    if is_blocked_either_way(sender, recipient):
        return False, 'blocked'
    if recipient.dm_privacy == User.DM_NOBODY:
        return False, 'nobody'
    if recipient.dm_privacy == User.DM_FOLLOWERS:
        if not Follow.objects.filter(follower=recipient, following=sender).exists():
            return False, 'followers_only'
    return True, None


def get_or_create_conversation(user_a, user_b):
    """Fetch an existing conversation, or create one initiated by `user_a`.
    Permission checks happen separately (see `can_message`) before this is
    called for a brand new conversation."""
    conversation = find_conversation(user_a, user_b)
    if conversation is not None:
        return conversation

    accepted = Follow.objects.filter(follower=user_b, following=user_a).exists()
    conversation = Conversation.objects.create(initiator=user_a, accepted=accepted)
    conversation.participants.add(user_a, user_b)
    return conversation


@login_required
def inbox_view(request):
    conversations = (
        request.user.conversations.all()
        .prefetch_related('participants', 'messages')
    )

    primary, requests_ = [], []
    for conversation in conversations:
        other = conversation.other_participant(request.user)
        if other is None:
            continue
        last = conversation.last_message()
        unread = conversation.messages.filter(is_read=False).exclude(sender=request.user).exists()
        row = {'conversation': conversation, 'other': other, 'last': last, 'unread': unread}
        (requests_ if conversation.is_request_for(request.user) else primary).append(row)

    sort_key = lambda r: r['last'].created_at if r['last'] else r['conversation'].created_at
    primary.sort(key=sort_key, reverse=True)
    requests_.sort(key=sort_key, reverse=True)

    return render(request, 'messaging/inbox.html', {'rows': primary, 'request_rows': requests_})


@login_required
def conversation_view(request, username):
    other = get_object_or_404(User, username=username)
    if other.id == request.user.id:
        raise PermissionDenied("You can't message yourself.")

    if is_blocked_either_way(request.user, other):
        return render(request, 'messaging/conversation.html', {
            'other': other, 'conversation': None, 'messages_list': [], 'deny_reason': 'blocked',
        })

    conversation = find_conversation(request.user, other)
    if conversation is None:
        allowed, reason = can_message(request.user, other)
        if not allowed:
            return render(request, 'messaging/conversation.html', {
                'other': other, 'conversation': None, 'messages_list': [], 'deny_reason': reason,
            })
        conversation = get_or_create_conversation(request.user, other)

    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    messages_list = conversation.messages.select_related('sender').all()

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'other': other,
        'messages_list': messages_list,
        'is_request': conversation.is_request_for(request.user),
    })


@login_required
@rate_limit('message', limit=60, window=60)
def send_message_view(request, username):
    other = get_object_or_404(User, username=username)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if other.id == request.user.id:
        return JsonResponse({'error': "You can't message yourself."}, status=400)
    if is_blocked_either_way(request.user, other):
        return JsonResponse({'error': 'You cannot message this user.'}, status=403)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
    if len(content) > 2000:
        return JsonResponse({'error': 'Message is too long.'}, status=400)

    conversation = find_conversation(request.user, other)
    if conversation is None:
        allowed, reason = can_message(request.user, other)
        if not allowed:
            return JsonResponse({'error': 'You cannot message this user.'}, status=403)
        conversation = get_or_create_conversation(request.user, other)
    elif not conversation.accepted and conversation.initiator_id != request.user.id:
        # The recipient replying to a message request implicitly accepts it.
        conversation.accepted = True
        conversation.save(update_fields=['accepted'])

    message = Message.objects.create(conversation=conversation, sender=request.user, content=content)

    return JsonResponse({
        'id': message.id,
        'content': message.content,
        'sender_username': request.user.username,
        'created_at': message.created_at.strftime('%H:%M'),
    })


@login_required
@rate_limit('message', limit=60, window=60)
def accept_request_view(request, username):
    other = get_object_or_404(User, username=username)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    conversation = find_conversation(request.user, other)
    if conversation is None or conversation.initiator_id == request.user.id:
        return JsonResponse({'error': 'Nothing to accept.'}, status=400)

    conversation.accepted = True
    conversation.save(update_fields=['accepted'])
    return JsonResponse({'accepted': True})


@login_required
def decline_request_view(request, username):
    other = get_object_or_404(User, username=username)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    conversation = find_conversation(request.user, other)
    if conversation is not None and conversation.initiator_id != request.user.id:
        conversation.delete()
    return JsonResponse({'declined': True})


@login_required
def poll_messages_view(request, username):
    other = get_object_or_404(User, username=username)
    after_id = request.GET.get('after', 0)
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    conversation = find_conversation(request.user, other)
    if conversation is None:
        return JsonResponse({'messages': []})

    new_messages = (
        conversation.messages.filter(id__gt=after_id)
        .exclude(sender=request.user)
        .select_related('sender')
    )
    new_messages.filter(is_read=False).update(is_read=True)

    return JsonResponse({
        'messages': [
            {
                'id': m.id,
                'content': m.content,
                'sender_username': m.sender.username,
                'created_at': m.created_at.strftime('%H:%M'),
            }
            for m in new_messages
        ]
    })


@login_required
def unread_messages_count_api(request):
    count = Message.objects.filter(
        conversation__participants=request.user, is_read=False
    ).exclude(sender=request.user).count()
    return JsonResponse({'count': count})
