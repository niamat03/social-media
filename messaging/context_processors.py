from django.db.models import Q

from .models import Message


def unread_messages_count(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            conversation__participants=request.user, is_read=False
        ).exclude(sender=request.user).filter(
            Q(conversation__accepted=True) | Q(conversation__initiator=request.user)
        ).count()
    else:
        count = 0
    return {'unread_messages_count': count}
