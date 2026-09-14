from django.contrib import admin

from .models import Block, Follow, Notification


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'blocker', 'blocked', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'actor', 'verb', 'is_read', 'created_at')
    list_filter = ('verb', 'is_read')
