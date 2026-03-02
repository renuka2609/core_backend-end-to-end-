from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role.lower() == "admin"
        )

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to Admin users.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Superuser always allowed
        if user.is_superuser:
            return True

        # Check group
        return user.groups.filter(name="Admin").exists()


class IsReviewer(BasePermission):
    """
    Allows access to Reviewer and Admin.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if user.groups.filter(name="Admin").exists():
            return True

        return user.groups.filter(name="Reviewer").exists()


class IsVendor(BasePermission):
    """
    Allows access only to Vendor.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(name="Vendor").exists()

class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role.lower() == "reviewer"
        )


class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role.lower() == "vendor"
        )


class IsAdminOrReviewer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role.lower() in ["admin", "reviewer"]
        )
