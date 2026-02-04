from rest_framework.permissions import BasePermission
from permissions.constants import Roles, Permissions


class IsAdminOrRequester(BasePermission):
    """Check if user is admin or requester"""
    def has_permission(self, request, view):
        return request.user.role in [Roles.ADMIN, Roles.REVIEWER]


class IsAdmin(BasePermission):
    """Check if user is admin"""
    def has_permission(self, request, view):
        return request.user.role == Roles.ADMIN


class IsVendor(BasePermission):
    """Check if user is vendor"""
    def has_permission(self, request, view):
        return request.user.role == Roles.VENDOR


class HasPermission(BasePermission):
    """Check if user has a specific permission"""
    required_permission = None
    
    def has_permission(self, request, view):
        if not self.required_permission:
            return True
        return Permissions.can_perform(request.user.role, self.required_permission)

