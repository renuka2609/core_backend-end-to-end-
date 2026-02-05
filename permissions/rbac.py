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


class IsAdminOrReviewer(BasePermission):
    """Check if user is admin or reviewer"""
    def has_permission(self, request, view):
        return request.user.role in [Roles.ADMIN, Roles.REVIEWER]


class CanCreateTemplate(BasePermission):
    """Only admins can create templates"""
    def has_permission(self, request, view):
        if request.method in ['POST']:
            return request.user.role == Roles.ADMIN
        return True


class CanCreateTemplateVersion(BasePermission):
    """Only admins can create template versions"""
    def has_permission(self, request, view):
        if request.method in ['POST']:
            return request.user.role == Roles.ADMIN
        return True


class CanSubmitAssessment(BasePermission):
    """Only vendors can submit assessments"""
    def has_permission(self, request, view):
        if view.action == 'submit':
            if getattr(request.user, 'role', None) != Roles.VENDOR:
                # Provide a helpful message for denied permissions
                self.message = "Only users with role 'VENDOR' can submit assessments"
                return False
            return True
        return True


class CanReviewAssessment(BasePermission):
    """Only reviewers and admins can review assessments"""
    def has_permission(self, request, view):
        if view.action == 'review':
            if getattr(request.user, 'role', None) not in [Roles.REVIEWER, Roles.ADMIN]:
                self.message = "Only users with role 'REVIEWER' or 'ADMIN' can review assessments"
                return False
            return True
        return True


class CanApproveAssessment(BasePermission):
    """Only admins can approve assessments"""
    def has_permission(self, request, view):
        if view.action == 'approve':
            if getattr(request.user, 'role', None) != Roles.ADMIN:
                self.message = "Only users with role 'ADMIN' can approve assessments"
                return False
            return True
        return True


class HasPermission(BasePermission):
    """Check if user has a specific permission"""
    required_permission = None
    
    def has_permission(self, request, view):
        if not self.required_permission:
            return True
        return Permissions.can_perform(request.user.role, self.required_permission)


