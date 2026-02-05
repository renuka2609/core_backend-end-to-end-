from rest_framework.permissions import BasePermission, SAFE_METHODS
from permissions.constants import Roles


class IsAdminOrReadOnly(BasePermission):
    """
    Admin → full access
    Others → read only (GET)
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == Roles.ADMIN

