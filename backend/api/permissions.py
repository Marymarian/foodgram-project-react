from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Доступ к чтение разрешен всем, на изменение - администраторам."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsAdminAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Доступ к чтению  разрешен всем, изменению - автору, администраторам."""
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (request.user == obj.author)
                or request.user.is_staff)