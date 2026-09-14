from django.contrib import admin

from .models import Comment, Hashtag, Like, Post, Report, SavedPost


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'city')
    search_fields = ('content', 'author__username', 'city')
    list_filter = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'created_at')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'created_at')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'reporter', 'reason', 'created_at', 'resolved')
    list_filter = ('resolved', 'reason')
    actions = ['mark_resolved']

    @admin.action(description='Mark selected reports as resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)
