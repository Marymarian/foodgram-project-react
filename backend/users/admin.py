from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Follow


class CustomUserAdmin(UserAdmin):
    """В админке: отобр. и фильтр полей User."""

    list_display = ("email", "username")
    list_filter = ("email", "username")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """В админке: отобр.,фильтр, поиск полей Follow."""

    list_display = ("id", "user", "author")
    search_fields = ("user", "author")
    list_filter = ("user", "author")


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
