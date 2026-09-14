from django.urls import path

from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('unread-count/', views.unread_messages_count_api, name='unread_count'),
    path('<str:username>/', views.conversation_view, name='conversation'),
    path('<str:username>/send/', views.send_message_view, name='send'),
    path('<str:username>/poll/', views.poll_messages_view, name='poll'),
]
