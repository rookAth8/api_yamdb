from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or (
                request.user.is_authenticated
                and request.user.is_admin
            )
        )


class IsRoleAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_admin or user.is_superuser)


class ReviewCommentCustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        elif isinstance(user, AnonymousUser):
            return False
        else:
            return user.is_authenticated or (
                user.is_admin or user.is_superuser or user.is_moderator
            )

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        elif isinstance(user, AnonymousUser):
            return False
        else:
            return obj.author == user or (
                user.is_admin or user.is_superuser or user.is_moderator
            )
