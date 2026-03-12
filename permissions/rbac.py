"""
Consolidated RBAC Permission Classes

This module re-exports the unified permission classes from rbac_policy.
All permission logic is now centralized in rbac_policy.py to avoid duplication.

For the central policy matrix and role definitions, see rbac_policy.py.
"""

from permissions.rbac_policy import (
    IsAdmin,
    IsReviewer,
    IsVendor,
    IsAdminOrReviewer,
    IsAuthenticated,
    WorkflowActionPermission,
    RoleType,
    WorkflowAction,
    RBACPolicyHelper,
    RBAC_POLICY_MATRIX,
    require_action,
)

__all__ = [
    "IsAdmin",
    "IsReviewer",
    "IsVendor",
    "IsAdminOrReviewer",
    "IsAuthenticated",
    "WorkflowActionPermission",
    "RoleType",
    "WorkflowAction",
    "RBACPolicyHelper",
    "RBAC_POLICY_MATRIX",
    "require_action",
]
