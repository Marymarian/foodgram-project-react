from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение администратору, на чтение-всем."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsAdminAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Разрешение дминистратору/автору, остальным чтение."""
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (request.user == obj.author)
                or request.user.is_staff)
