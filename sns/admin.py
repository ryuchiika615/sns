from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import UserLoginSession, Post, Profile, GachaItem, Comment, Notification


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)


@admin.register(UserLoginSession)
class UserLoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_at', 'last_seen_at', 'logout_at', 'ip_address')
    list_filter = ('login_at', 'logout_at')
    search_fields = ('user__username', 'ip_address')
    date_hierarchy = 'login_at'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content_short', 'subject', 'study_minutes', 'created_at')
    list_filter = ('subject', 'created_at', 'user')
    search_fields = ('content', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    def content_short(self, obj):
        return obj.content[:30]
    content_short.short_description = '内容'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'department', 'points', 'exchange_points')
    list_filter = ('department', 'theme_color')
    search_fields = ('user__username', 'display_name', 'bio')
    readonly_fields = ('points', 'exchange_points')


@admin.register(GachaItem)
class GachaItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'rarity')
    list_filter = ('rarity',)
    search_fields = ('name',)
    ordering = ('rarity', 'name')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'text_short', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username')
    date_hierarchy = 'created_at'

    def text_short(self, obj):
        return obj.text[:30]
    text_short.short_description = 'コメント'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username')
    date_hierarchy = 'created_at'
