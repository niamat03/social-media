from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('saved/', views.saved_posts_view, name='saved'),
    path('hashtag/<str:name>/', views.hashtag_view, name='hashtag'),
    path('post/<int:pk>/', views.post_detail_view, name='detail'),
    path('post/<int:pk>/edit/', views.edit_post_view, name='edit'),
    path('post/<int:pk>/delete/', views.delete_post_view, name='delete'),
    path('post/<int:pk>/like/', views.like_toggle_view, name='like_toggle'),
    path('post/<int:pk>/save/', views.save_toggle_view, name='save_toggle'),
    path('post/<int:pk>/report/', views.report_post_view, name='report'),
    path('post/<int:pk>/comment/', views.add_comment_view, name='add_comment'),
    path('comment/<int:pk>/edit/', views.edit_comment_view, name='edit_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment_view, name='delete_comment'),
]
