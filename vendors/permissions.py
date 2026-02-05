from rest_framework.permissions import BasePermission
from permissions.constants import Roles


class CanCreateVendor(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.role in [Roles.ADMIN, Roles.REVIEWER]
        return True

