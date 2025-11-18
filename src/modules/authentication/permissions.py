from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "clerk_role", None) == "admin"
