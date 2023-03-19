from django.contrib import admin
from .models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """В админке: отображение, поиск, фильтр полей User."""
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """В админке: отображение, поиск, фильтр полей Follow."""
    list_display = ('pk', 'user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
