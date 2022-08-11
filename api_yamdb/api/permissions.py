from rest_framework import permissions


class IsRoleAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_admin or user.is_superuser)
