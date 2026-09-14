from django.urls import path

from . import views

app_name = 'social'

urlpatterns = [
    path('users/<str:username>/follow/', views.follow_toggle_view, name='follow_toggle'),
    path('users/<str:username>/block/', views.block_toggle_view, name='block_toggle'),
    path('explore/', views.explore_view, name='explore'),
    path('search/', views.search_view, name='search'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/unread-count/', views.unread_notifications_count_api, name='unread_notifications_count'),
]
