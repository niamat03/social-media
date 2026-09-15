from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.AccountLoginView.as_view(), name='login'),
    path('logout/', views.AccountLogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/<str:username>/followers/', views.followers_view, name='followers'),
    path('profile/<str:username>/following/', views.following_view, name='following'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
]
