# RBAC Implementation - Code Location Reference

**For:** Developers needing to verify or modify permission checks  
**Last Updated:** April 4, 2026

---

## Permission Class Definitions

### Central Definitions

**Location:** `permissions/rbac_policy.py`

| Class | Lines | Base Class | Purpose |
|-------|-------|-----------|---------|
| `RoleType` (Enum) | 16-19 | `Enum` | Role types: ADMIN, REVIEWER, VENDOR, VIEWER |
| `WorkflowAction` (Enum) | 22-76 | `Enum` | All workflow actions across system |
| `RBAC_POLICY_MATRIX` (Dict) | 89-142 | N/A | Central policy mapping actions→roles |
| `RBACPolicyHelper` (Class) | 145-181 | N/A | Utility methods for role/action checks |
| `IsAdmin` | 199-206 | `BasePermission` | Admin-only access |
| `IsReviewer` | 210-218 | `BasePermission` | Admin + Reviewer access |
| `IsVendor` | 221-229 | `BasePermission` | Vendor-only access |
| `IsAdminOrReviewer` | 232-240 | `BasePermission` | Admin or Reviewer access |
| `IsAuthenticated` | 243-248 | `BasePermission` | Any authenticated user |
| `WorkflowActionPermission` | 254-297 | `BasePermission` | Policy matrix-based validation |

### Re-exports

**Location:** `permissions/rbac.py` (Lines 1-37)
- Re-exports all major classes from `rbac_policy.py`
- Import here instead of directly from `rbac_policy.py`

### Role Constants

**Location:** `permissions/constants.py` (Lines 1-45)

| Constant Set | Lines |
|--------------|-------|
| `Roles` class | 4-16 |
| `Roles.ADMIN` | 5 |
| `Roles.REVIEWER` | 6 |
| `Roles.VENDOR` | 7 |
| `Roles.CHOICES` | 9-13 |
| `Permissions` class | 19-45 |

### App-Specific Permission Classes

| Class | File | Lines | Purpose |
|-------|------|-------|---------|
| `IsAdminOrReadOnly` | `accounts/permissions.py` | 4-13 | Admin modify, others read-only |
| `CanCreateVendor` | `vendors/permissions.py` | 5-14 | Vendor creation check |

---

## ViewSet Implementations

### Assessment ViewSet

**File:** `assessments/views.py`  
**Class:** `AssessmentViewSet` (Lines 18-135)

| Method | Lines | Permission Check | Action |
|--------|-------|------------------|--------|
| Class definition | 18-20 | `IsAuthenticated` | N/A |
| `perform_create()` | 22-28 | `ASSESSMENT_CREATE` | Create assessment |
| `submit()` action | 55-65 | `ASSESSMENT_SUBMIT` | Vendor submits |
| `review()` action | 71-81 | `ASSESSMENT_REVIEW` | Admin/Reviewer reviews |
| `approve()` action | 87-113 | `ASSESSMENT_APPROVE` | Admin/Reviewer approves |
| `remediate()` action | 122-135 | `ASSESSMENT_REVIEW` | Request remediation |

**Import Statement:** Line 9-13

---

### Reviews ViewSet

**File:** `reviews/views.py`  
**Class:** `ReviewViewSet` (Lines 14-31)

| Method | Lines | Permission Check | Access |
|--------|-------|------------------|--------|
| Class definition | 14-18 | `IsAuthenticated, IsReviewer` | N/A |
| `decision()` action | 20-31 | `REVIEW_DECIDE` | Make decision |

**Import Statement:** Lines 4-10

---

### Vendors ViewSet

**File:** `vendors/views.py`  
**Class:** `VendorViewSet` (Lines 13-23)

| Method | Lines | Permission Check | Access |
|--------|-------|------------------|--------|
| Class definition | 13-16 | `IsAuthenticated, IsAdmin` | N/A |
| `perform_create()` | 18-23 | `VENDOR_CREATE` | Create vendor |

**Import Statement:** Lines 2-8

---

### Templates ViewSet

**File:** `templates/views.py`  
**Class:** `TemplateViewSet` (Lines 8-15)

| Method | Lines | Permission Check | Status |
|--------|-------|------------------|--------|
| Class definition | 8-11 | `IsAuthenticated` | ⚠️ Missing role check |
| `perform_create()` | 13-14 | ❌ None | ⚠️ Should add check |

**Issue:** No `WorkflowActionPermission` checks  
**Import Statement:** Lines 1-5

---

### Responses ViewSet

**File:** `responses/views.py`  
**Class:** `ResponseViewSet` (Lines 11-61)

| Method | Lines | Permission Check | Status |
|--------|-------|------------------|--------|
| Class definition | 11-17 | `IsAuthenticated` | ⚠️ No role check |
| `perform_create()` | 19-28 | ❌ None | ⚠️ Missing |
| `perform_update()` | 30-39 | ❌ None | ⚠️ Missing |
| `submit()` action | 43-61 | ❌ None | ⚠️ Missing |

**Issue:** No `WorkflowActionPermission` checks  
**Import Statement:** Lines 1-9

---

### Evidence ViewSet

**File:** `evidence/views.py`  
**Class:** `EvidenceViewSet` (Lines 10-51)

| Method | Lines | Permission Check | Status |
|--------|-------|------------------|--------|
| Class definition | 10-13 | `IsAuthenticated` | ⚠️ No role check |
| `perform_create()` | 15-23 | ❌ None | ⚠️ Missing |
| `perform_update()` | 25-32 | ❌ None | ⚠️ Missing |
| `perform_destroy()` | 34-42 | ❌ None | ⚠️ Missing |

**Issue:** No `WorkflowActionPermission` checks  
**Import Statement:** Lines 1-8

---

### Remediations ViewSet

**File:** `remediations/views.py`  
**Class:** `RemediationViewSet` (Lines 13-58)

| Method | Lines | Permission Check | Status |
|--------|-------|------------------|--------|
| Class definition | 13-14 | ❌ None | 🔴 CRITICAL |
| `perform_create()` | 16-22 | ❌ None | 🔴 CRITICAL |
| `respond()` action | 25-36 | ❌ None | 🔴 CRITICAL |
| `close()` action | 39-50 | ❌ None | 🔴 CRITICAL |

**Issue:** No `permission_classes` defined + no workflow checks  
**Import Statement:** Lines 1-11

---

### Dashboard Views

**File:** `dashboard/views.py`

| Class | Lines | Permission Check | Status |
|-------|-------|------------------|--------|
| `DashboardStatsView` | 9-26 | `IsAuthenticated` (no role check) | ⚠️ Missing stats role check |
| `DashboardActivityFeedView` | 28-45 | `IsAuthenticated` | Could add view role check |

**Issue:** No role-based filtering for stats endpoint

---

### Audit ViewSet

**File:** `audit/views.py`  
**Class:** `AuditEventViewSet` (Lines 33-152)

| Feature | Lines | Implementation | Status |
|---------|-------|-----------------|--------|
| Class definition | 33-73 | `[IsAuthenticated]` only | ⚠️ No tenant filter |
| `get_queryset()` | N/A | Uses default from class | ⚠️ No org filtering |
| `list()` | 75-90 | Read-only list | ⚠️ Missing mixin |
| `by_resource()` | 92-131 | Custom action | ⚠️ No org filter |
| `by_user()` | 133-152 | Custom action | ⚠️ No org filter |

**Issue:** No tenant isolation enforcement

---

## Tenant Guard Implementation

**File:** `permissions/tenant_guard.py`

| Class | Lines | Purpose |
|-------|-------|---------|
| `TenantAwareQueryGuardMixin` | 12-119 | Mixin for tenant filtering on list/detail |
| `get_tenant_value()` | 25-39 | Extract user's tenant |
| `get_queryset()` | 42-56 | Filter list queries by tenant |
| `get_object()` | 59-75 | Verify object belongs to tenant |
| `_verify_object_belongs_to_tenant()` | 78-96 | Check object-tenant relationship |
| `TenantFilterPermission` | 100-164 | Object-level permission check |

**Usage in ViewSets:**
```python
class MyViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    tenant_filter_field = 'org'  # Simple field
    # OR
    tenant_lookup_path = 'assessment__org'  # Nested relationship
```

**Current Usage:**
- ✅ `AssessmentViewSet` - Line 18
- ✅ `ReviewViewSet` - Line 14
- ✅ `VendorViewSet` - Line 13
- ✅ `TemplateViewSet` - Line 8
- ✅ `ResponseViewSet` - Line 11
- ✅ `EvidenceViewSet` - Line 10
- ✅ `RemediationViewSet` - Line 13
- ❌ `AuditEventViewSet` - Missing
- ❌ `DashboardViews` - N/A (custom views)

---

## Workflow Action Usage Locations

**File:** `permissions/rbac_policy.py`

### Policy Matrix (Lines 89-142)

| Action Category | Action Names | Lines |
|-----------------|--------------|-------|
| Assessment | 8 actions | 91-98 |
| Review | 5 actions | 101-105 |
| Evidence | 4 actions | 108-111 |
| Response | 5 actions | 114-118 |
| Remediation | 6 actions | 121-126 |
| Template | 4 actions | 129-132 |
| Vendor | 4 actions | 135-138 |
| Dashboard | 2 actions | 141-142 |

### Action Usages

| Action | Used In | File | Lines |
|--------|---------|------|-------|
| `ASSESSMENT_CREATE` | perform_create | assessments/views.py | 26-27 |
| `ASSESSMENT_SUBMIT` | submit() | assessments/views.py | 60 |
| `ASSESSMENT_REVIEW` | review(), remediate() | assessments/views.py | 76, 127 |
| `ASSESSMENT_APPROVE` | approve() | assessments/views.py | 92 |
| `REVIEW_DECIDE` | decision() | reviews/views.py | 26 |
| `VENDOR_CREATE` | perform_create | vendors/views.py | 23 |

---

## Helper Method References

### RBACPolicyHelper Methods

**Location:** `permissions/rbac_policy.py`, Lines 145-181

| Method | Lines | Parameters | Returns | Purpose |
|--------|-------|-----------|---------|---------|
| `get_user_role()` | 152-177 | `user` | `RoleType` | Extract role from user, handling multipl fallback strategies |
| `can_perform_action()` | 179-184 | `user, action` | `bool` | Checks if user can perform action |
| `get_allowed_roles()` | 186-188 | `action` | `set` | Returns allowed roles for action |

### WorkflowActionPermission Methods

**Location:** `permissions/rbac_policy.py`, Lines 254-297

| Method | Lines | Type | Purpose |
|--------|-------|------|---------|
| `check_action()` | 285-287 | Static | Check if user can perform action (returns bool) |
| `check_action_or_raise()` | 289-297 | Static | Check and raise PermissionDenied if not allowed |
| `has_permission()` | 273-280 | Instance | DRF integration for permission checking |

---

## Import Reference Guide

### Correct Imports by File Type

#### For ViewSets
```python
# Line 1-2
from rest_framework.permissions import IsAuthenticated
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
    # Optional: If restricting at class level:
    # IsAdmin,
    # IsReviewer,
    # IsAdminOrReviewer,
)
# Line 3
from permissions.tenant_guard import TenantAwareQueryGuardMixin
```

#### For Permission Classes
```python
from rest_framework.permissions import BasePermission
from permissions.constants import Roles
```

#### For Helper Methods
```python
from permissions.rbac_policy import (
    RBACPolicyHelper,
    RoleType,
    WorkflowAction,
)
```

---

## Quick Navigation

### Find Permission Issues
1. **Check for permission_classes:** Search for `permission_classes =` in `views.py`
2. **Check for workflow actions:** Search for `WorkflowAction.` in `views.py`
3. **Check for tenant guard:** Search for `TenantAwareQueryGuardMixin` in `views.py`
4. **Check for role constants:** Search for `Roles.` in files

### Find All Permission Definitions
```bash
# Search for all permission classes
grep -r "class.*Permission" --include="*.py" permissions/

# Find all role checks
grep -r "WorkflowAction\." --include="*.py"

# Find all usage of permission_classes
grep -r "permission_classes" --include="*.py"
```

### Files That Need Changes
1. `remediations/views.py` - P0
2. `responses/views.py` - P1
3. `evidence/views.py` - P1  
4. `templates/views.py` - P1
5. `dashboard/views.py` - P2
6. `audit/views.py` - P2

---

## Testing Locations

### Existing Tests
- `assessments/tests.py` - Test assessment permissions
- `reviews/tests.py` - Test review permissions
- `vendors/tests.py` - Test vendor permissions
- Various test files in each app directory

### Where to Write New Tests
```python
# Test file location: <app>/tests.py

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from users.models import User
from permissions.constants import Roles

class PermissionTests(APITestCase):
    def test_vendor_cannot_create_template(self):
        # Create vendor user
        vendor = User.objects.create(role=Roles.VENDOR, org_id=1)
        
        # Try to create template
        response = self.client.post('/api/templates/', {...}, 
                                    HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Should be 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

---

## Reference Documents

| Document | Purpose | Location |
|----------|---------|----------|
| Implementation Summary | Full architectural overview | `RBAC_IMPLEMENTATION_SUMMARY.md` |
| Quick Reference | Developer quick-lookup guide | `RBAC_QUICK_REFERENCE.md` |
| Issues & Actions | Detailed problem list with fixes | `RBAC_ISSUES_AND_ACTION_ITEMS.md` |
| This Document | Code location reference | `RBAC_CODE_LOCATION_REFERENCE.md` |

---

**Last Updated:** April 4, 2026  
**Version:** 1.0
