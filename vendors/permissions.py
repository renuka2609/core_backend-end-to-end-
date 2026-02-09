from rest_framework.permissions import BasePermission
from permissions.constants import Roles


class CanCreateVendor(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                return False
            user_role = getattr(user, "role", None)
            return user_role in [Roles.ADMIN, Roles.REVIEWER]

        return True

