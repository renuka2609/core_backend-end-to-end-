"""
Central RBAC Policy Layer

This module defines the unified role-based access control (RBAC) policy matrix
for the entire system. It replaces scattered permission checks with a single
source of truth for what each role can do.

Architecture:
  - RoleType: Enum of all valid roles
  - WorkflowAction: Enum of all workflow actions
  - RBAC_POLICY_MATRIX: Central config of who can do what
  - Permission classes use the policy matrix
"""

from enum import Enum
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class RoleType(Enum):
    """Valid role types in the system."""
    ADMIN = "admin"
    REVIEWER = "reviewer"
    VENDOR = "vendor"
    VIEWER = "viewer"


class WorkflowAction(Enum):
    """Workflow actions across the system."""
    # Assessment workflow
    ASSESSMENT_CREATE = "assessment:create"
    ASSESSMENT_VIEW = "assessment:view"
    ASSESSMENT_EDIT = "assessment:edit"
    ASSESSMENT_DELETE = "assessment:delete"
    ASSESSMENT_SUBMIT = "assessment:submit"
    ASSESSMENT_REVIEW = "assessment:review"
    ASSESSMENT_APPROVE = "assessment:approve"
    ASSESSMENT_REJECT = "assessment:reject"
    
    # Review workflow
    REVIEW_CREATE = "review:create"
    REVIEW_VIEW = "review:view"
    REVIEW_EDIT = "review:edit"
    REVIEW_DELETE = "review:delete"
    REVIEW_DECIDE = "review:decide"
    
    # Evidence workflow
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_VIEW = "evidence:view"
    EVIDENCE_EDIT = "evidence:edit"
    EVIDENCE_DELETE = "evidence:delete"
    
    # Response workflow
    RESPONSE_CREATE = "response:create"
    RESPONSE_VIEW = "response:view"
    RESPONSE_EDIT = "response:edit"
    RESPONSE_DELETE = "response:delete"
    RESPONSE_SUBMIT = "response:submit"
    
    # Remediation workflow
    REMEDIATION_CREATE = "remediation:create"
    REMEDIATION_VIEW = "remediation:view"
    REMEDIATION_EDIT = "remediation:edit"
    REMEDIATION_DELETE = "remediation:delete"
    REMEDIATION_RESPOND = "remediation:respond"
    REMEDIATION_CLOSE = "remediation:close"
    
    # Template workflow
    TEMPLATE_CREATE = "template:create"
    TEMPLATE_VIEW = "template:view"
    TEMPLATE_EDIT = "template:edit"
    TEMPLATE_DELETE = "template:delete"
    
    # Vendor workflow
    VENDOR_CREATE = "vendor:create"
    VENDOR_VIEW = "vendor:view"
    VENDOR_EDIT = "vendor:edit"
    VENDOR_DELETE = "vendor:delete"
    
    # Dashboard
    DASHBOARD_VIEW = "dashboard:view"
    DASHBOARD_STATS = "dashboard:stats"


# ============================================================================
# RBAC POLICY MATRIX: Define which roles can perform which actions
# ============================================================================
# Each WorkflowAction maps to a set of RoleTypes allowed to perform it
RBAC_POLICY_MATRIX = {
    # ========== Assessment Workflow ==========
    WorkflowAction.ASSESSMENT_CREATE: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.ASSESSMENT_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR, RoleType.VIEWER},
    WorkflowAction.ASSESSMENT_EDIT: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.ASSESSMENT_DELETE: {RoleType.ADMIN},
    WorkflowAction.ASSESSMENT_SUBMIT: {RoleType.VENDOR},
    WorkflowAction.ASSESSMENT_REVIEW: {RoleType.ADMIN, RoleType.REVIEWER},
    WorkflowAction.ASSESSMENT_APPROVE: {RoleType.ADMIN, RoleType.REVIEWER},
    WorkflowAction.ASSESSMENT_REJECT: {RoleType.ADMIN, RoleType.REVIEWER},
    
    # ========== Review Workflow ==========
    WorkflowAction.REVIEW_CREATE: {RoleType.ADMIN, RoleType.REVIEWER},
    WorkflowAction.REVIEW_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR},
    WorkflowAction.REVIEW_EDIT: {RoleType.ADMIN, RoleType.REVIEWER},
    WorkflowAction.REVIEW_DELETE: {RoleType.ADMIN},
    WorkflowAction.REVIEW_DECIDE: {RoleType.ADMIN, RoleType.REVIEWER},
    
    # ========== Evidence Workflow ==========
    WorkflowAction.EVIDENCE_CREATE: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.EVIDENCE_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR},
    WorkflowAction.EVIDENCE_EDIT: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.EVIDENCE_DELETE: {RoleType.ADMIN, RoleType.VENDOR},
    
    # ========== Response Workflow ==========
    WorkflowAction.RESPONSE_CREATE: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.RESPONSE_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR},
    WorkflowAction.RESPONSE_EDIT: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.RESPONSE_DELETE: {RoleType.ADMIN, RoleType.VENDOR},
    WorkflowAction.RESPONSE_SUBMIT: {RoleType.VENDOR},
    
    # ========== Remediation Workflow ==========
    WorkflowAction.REMEDIATION_CREATE: {RoleType.ADMIN, RoleType.REVIEWER},
    WorkflowAction.REMEDIATION_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR},
    WorkflowAction.REMEDIATION_EDIT: {RoleType.ADMIN, RoleType.REVIEWER},
    WorkflowAction.REMEDIATION_DELETE: {RoleType.ADMIN},
    WorkflowAction.REMEDIATION_RESPOND: {RoleType.VENDOR},
    WorkflowAction.REMEDIATION_CLOSE: {RoleType.ADMIN, RoleType.REVIEWER},
    
    # ========== Template Workflow ==========
    WorkflowAction.TEMPLATE_CREATE: {RoleType.ADMIN},
    WorkflowAction.TEMPLATE_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR},
    WorkflowAction.TEMPLATE_EDIT: {RoleType.ADMIN},
    WorkflowAction.TEMPLATE_DELETE: {RoleType.ADMIN},
    
    # ========== Vendor Workflow ==========
    WorkflowAction.VENDOR_CREATE: {RoleType.ADMIN},
    WorkflowAction.VENDOR_VIEW: {RoleType.ADMIN},
    WorkflowAction.VENDOR_EDIT: {RoleType.ADMIN},
    WorkflowAction.VENDOR_DELETE: {RoleType.ADMIN},
    
    # ========== Dashboard ==========
    WorkflowAction.DASHBOARD_VIEW: {RoleType.ADMIN, RoleType.REVIEWER, RoleType.VENDOR},
    WorkflowAction.DASHBOARD_STATS: {RoleType.ADMIN, RoleType.REVIEWER},
}


class RBACPolicyHelper:
    """Helper methods for RBAC policy operations."""
    
    @staticmethod
    def get_user_role(user) -> RoleType:
        """Extract user's role as RoleType enum."""
        if not user or not user.is_authenticated:
            return None
        
        # Superuser gets admin role
        if user.is_superuser:
            return RoleType.ADMIN
        
        # Try role attribute
        if hasattr(user, 'role') and user.role:
            role_name = user.role.lower()
            try:
                return RoleType(role_name)
            except ValueError:
                pass
        
        # Try group-based role
        if hasattr(user, 'groups'):
            for group in user.groups.all():
                role_name = group.name.lower()
                try:
                    return RoleType(role_name)
                except ValueError:
                    pass
        
        # Default to viewer
        return RoleType.VIEWER
    
    @staticmethod
    def can_perform_action(user, action: WorkflowAction) -> bool:
        """Check if user can perform the given action."""
        user_role = RBACPolicyHelper.get_user_role(user)
        if not user_role:
            return False
        
        allowed_roles = RBAC_POLICY_MATRIX.get(action, set())
        return user_role in allowed_roles
    
    @staticmethod
    def get_allowed_roles(action: WorkflowAction) -> set:
        """Get all roles allowed to perform an action."""
        return RBAC_POLICY_MATRIX.get(action, set())


# ============================================================================
# Consolidated Permission Classes
# ============================================================================

class IsAdmin(BasePermission):
    """Allow access only to Admin users."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = RBACPolicyHelper.get_user_role(user)
        return role == RoleType.ADMIN


class IsReviewer(BasePermission):
    """Allow access to Reviewer and Admin."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = RBACPolicyHelper.get_user_role(user)
        return role in {RoleType.ADMIN, RoleType.REVIEWER}


class IsVendor(BasePermission):
    """Allow access to Vendor users."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = RBACPolicyHelper.get_user_role(user)
        return role == RoleType.VENDOR


class IsAdminOrReviewer(BasePermission):
    """Allow access to Admin or Reviewer."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = RBACPolicyHelper.get_user_role(user)
        return role in {RoleType.ADMIN, RoleType.REVIEWER}


class IsAdminOrVendor(BasePermission):
    """Allow access to Admin or Vendor."""
    
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        role = RBACPolicyHelper.get_user_role(user)
        return role in {RoleType.ADMIN, RoleType.VENDOR}


class IsAuthenticated(BasePermission):
    """Allow access to any authenticated user."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


# ============================================================================
# Workflow Action Permission: Use policy matrix for custom actions
# ============================================================================

class WorkflowActionPermission(BasePermission):
    """
    Permission class for workflow actions.
    
    Usage:
        @action(detail=True, methods=["post"], 
                permission_classes=[WorkflowActionPermission])
        def submit(self, request, pk=None):
            # Before action, check permission
            if not WorkflowActionPermission.check_action(
                request.user, WorkflowAction.ASSESSMENT_SUBMIT
            ):
                raise PermissionDenied("Not authorized to submit assessment")
            ...
    """
    
    # Subclasses should set this
    required_action: WorkflowAction = None
    
    def has_permission(self, request, view):
        """Check if user has permission for the configured action."""
        if not self.required_action:
            return False
        
        if not RBACPolicyHelper.can_perform_action(request.user, self.required_action):
            return False
        
        return True
    
    @staticmethod
    def check_action(user, action: WorkflowAction) -> bool:
        """Standalone method to check if user can perform action."""
        return RBACPolicyHelper.can_perform_action(user, action)
    
    @staticmethod
    def check_action_or_raise(user, action: WorkflowAction) -> None:
        """Check action and raise PermissionDenied if not allowed."""
        if not RBACPolicyHelper.can_perform_action(user, action):
            allowed_roles = RBACPolicyHelper.get_allowed_roles(action)
            role_names = ", ".join([r.value for r in allowed_roles])
            raise PermissionDenied(
                f"Not authorized to perform '{action.value}'. "
                f"Required roles: {role_names}"
            )


# ============================================================================
# Helper Function for Use in Views
# ============================================================================

def require_action(action: WorkflowAction):
    """
    Decorator to require a workflow action permission.
    
    Usage:
        @require_action(WorkflowAction.ASSESSMENT_APPROVE)
        def approve(self, request, pk=None):
            ...
    """
    def decorator(view_func):
        def wrapper(self, request, *args, **kwargs):
            WorkflowActionPermission.check_action_or_raise(request.user, action)
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator
