from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from config.throttle import rate_limit
from social.block_utils import is_blocked_either_way

from .models import Conversation, Message

User = get_user_model()


def get_or_create_conversation(user_a, user_b):
    # Chaining two .filter(participants=...) calls on the same M2M produces two
    # separate joins; annotating Count('participants') afterwards double-counts
    # rows from that join multiplication, so the exact-pair check is done in
    # Python instead of via a single annotated queryset.
    candidates = Conversation.objects.filter(participants=user_a).filter(participants=user_b)
    for candidate in candidates:
        if candidate.participants.count() == 2:
            return candidate

    conversation = Conversation.objects.create()
    conversation.participants.add(user_a, user_b)
    return conversation


@login_required
def inbox_view(request):
    conversations = (
        request.user.conversations.all()
        .prefetch_related('participants', 'messages')
    )

    rows = []
    for conversation in conversations:
        other = conversation.other_participant(request.user)
        if other is None:
            continue
        last = conversation.last_message()
        unread = conversation.messages.filter(is_read=False).exclude(sender=request.user).exists()
        rows.append({
            'conversation': conversation,
            'other': other,
            'last': last,
            'unread': unread,
        })

    rows.sort(key=lambda r: r['last'].created_at if r['last'] else r['conversation'].created_at, reverse=True)

    return render(request, 'messaging/inbox.html', {'rows': rows})


@login_required
def conversation_view(request, username):
    other = get_object_or_404(User, username=username)
    if other.id == request.user.id:
        raise PermissionDenied("You can't message yourself.")

    conversation = get_or_create_conversation(request.user, other)
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    messages_list = conversation.messages.select_related('sender').all()

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'other': other,
        'messages_list': messages_list,
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

    conversation = get_or_create_conversation(request.user, other)
    message = Message.objects.create(conversation=conversation, sender=request.user, content=content)

    return JsonResponse({
        'id': message.id,
        'content': message.content,
        'sender_username': request.user.username,
        'created_at': message.created_at.strftime('%H:%M'),
    })


@login_required
def poll_messages_view(request, username):
    other = get_object_or_404(User, username=username)
    after_id = request.GET.get('after', 0)
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0

    conversation = get_or_create_conversation(request.user, other)
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
