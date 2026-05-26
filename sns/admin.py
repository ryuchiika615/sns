from django.contrib import admin
from .models import UserLoginSession


@admin.register(UserLoginSession)
class UserLoginSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_at', 'last_seen_at', 'logout_at', 'ip_address')
    list_filter = ('login_at', 'logout_at')
    search_fields = ('user__username', 'ip_address')
