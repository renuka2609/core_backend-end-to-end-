# RBAC Quick Reference Guide

**For:** Developers adding new endpoints or verifying permissions  
**Last Updated:** April 4, 2026

---

## Quick Lookup Tables

### By Role - What Can They Do?

#### 👑 ADMIN
- Create/Edit/Delete everything
- Review & approve assessments
- Create & manage reviews
- Create & manage templates
- Create & manage vendors
- Create remediations
- View all audit logs
- View admin dashboard stats

#### 🔍 REVIEWER
- View all assessments, reviews, evidence, responses, remediations
- Review and approve/reject assessments
- Create reviews and remediations
- Close remediations
- View audit logs (own org)
- View dashboard stats

#### 🏭 VENDOR
- Create assessments
- Edit own assessments
- Submit assessments for review
- Create evidence and responses
- Submit responses
- Respond to remediations
- View assigned assessments/reviews/remediations
- View templates
- View dashboard

---

## Permission Classes Cheat Sheet

### Use This | For This
```python
# 1. Simple authentication only
permission_classes = [IsAuthenticated]
# → All logged-in users can access

# 2. Admin-only access
permission_classes = [IsAuthenticated, IsAdmin]
# → Only admins

# 3. Reviewer + Admin
permission_classes = [IsAuthenticated, IsReviewer]
# → Admins and reviewers only

# 4. Vendor-only
permission_classes = [IsAuthenticated, IsVendor]
# → Only vendors

# 5. Action-specific validation
@action(detail=True, methods=["post"])
def my_action(self, request, pk=None):
    WorkflowActionPermission.check_action_or_raise(
        request.user,
        WorkflowAction.ASSESSMENT_SUBMIT
    )
    # ... logic
```

---

## How to Add Permission Checks

### Pattern 1: Class-Level (Simple Cases)

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from permissions.rbac_policy import IsAdmin
from permissions.tenant_guard import TenantAwareQueryGuardMixin

class MyViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]
    tenant_filter_field = 'org'
    
    # All endpoints now require IsAdmin access
```

**When to use:** For standard CRUD operations on admin-only resources.

---

### Pattern 2: Action-Level (Complex Cases)

```python
from rest_framework.decorators import action
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
)

class AssessmentViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Check role before create
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.ASSESSMENT_CREATE
        )
        serializer.save(org=self.request.user.org)
    
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        # Check role for this action
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.ASSESSMENT_SUBMIT
        )
        # ... do the action
```

**When to use:** When different CRUD operations have different role requirements.

---

### Pattern 3: Mixed Approach

```python
class ReviewViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    # Basic access: Reviewers + Admins
    permission_classes = [IsAuthenticated, IsReviewer]
    
    @action(detail=True, methods=["post"])
    def decision(self, request, pk=None):
        # Extra validation for the decide action
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.REVIEW_DECIDE
        )
        # ... make decision
```

**When to use:** When most operations use one permission but specific actions need extra checks.

---

## Workflow Action Matrix - All Actions

### Assessment Domain
```
ASSESSMENT_CREATE     → ADMIN, VENDOR
ASSESSMENT_SUBMIT     → VENDOR only
ASSESSMENT_REVIEW     → ADMIN, REVIEWER
ASSESSMENT_APPROVE    → ADMIN, REVIEWER
ASSESSMENT_REJECT     → ADMIN, REVIEWER
```

### Review Domain
```
REVIEW_CREATE    → ADMIN, REVIEWER
REVIEW_DECIDE    → ADMIN, REVIEWER (approve/reject review result)
```

### Evidence Domain
```
EVIDENCE_CREATE  → ADMIN, VENDOR
EVIDENCE_EDIT    → ADMIN, VENDOR
EVIDENCE_DELETE  → ADMIN, VENDOR
```

### Response Domain
```
RESPONSE_CREATE  → ADMIN, VENDOR
RESPONSE_SUBMIT  → VENDOR only
```

### Remediation Domain
```
REMEDIATION_CREATE   → ADMIN, REVIEWER
REMEDIATION_RESPOND  → VENDOR only
REMEDIATION_CLOSE    → ADMIN, REVIEWER
```

### Template Domain
```
TEMPLATE_CREATE  → ADMIN only
TEMPLATE_EDIT    → ADMIN only
TEMPLATE_DELETE  → ADMIN only
```

### Vendor Management
```
VENDOR_CREATE  → ADMIN only
VENDOR_EDIT    → ADMIN only
VENDOR_DELETE  → ADMIN only
```

---

## Common Checks - Code Examples

### Check if user can perform action
```python
from permissions.rbac_policy import WorkflowActionPermission, WorkflowAction

if WorkflowActionPermission.check_action(user, WorkflowAction.ASSESSMENT_SUBMIT):
    # User can submit
    pass
else:
    # User cannot submit
    pass
```

### Check and raise if not allowed
```python
from permissions.rbac_policy import WorkflowActionPermission, WorkflowAction

try:
    WorkflowActionPermission.check_action_or_raise(
        user,
        WorkflowAction.ASSESSMENT_APPROVE
    )
    # Proceed with action
except PermissionDenied as e:
    return Response({"error": str(e)}, status=403)
```

### Get allowed roles for action
```python
from permissions.rbac_policy import RBACPolicyHelper, WorkflowAction

allowed_roles = RBACPolicyHelper.get_allowed_roles(
    WorkflowAction.ASSESSMENT_CREATE
)
# Returns: {RoleType.ADMIN, RoleType.VENDOR}
```

### Get user's role
```python
from permissions.rbac_policy import RBACPolicyHelper, RoleType

user_role = RBACPolicyHelper.get_user_role(request.user)
# Returns: RoleType.ADMIN | RoleType.REVIEWER | etc.

if user_role == RoleType.ADMIN:
    # Admin-only logic
    pass
```

---

## Testing Tips

### Mock user with specific role
```python
from rest_framework.test import APIRequestFactory
from users.models import User
from permissions.constants import Roles

# Create mock factory
factory = APIRequestFactory()

# Create mock user
request = factory.get('/api/assessments/')
request.user = User(role=Roles.ADMIN, org_id=1)
```

### Test permission denied
```python
from rest_framework.test import force_authenticate
from rest_framework import status

# Create vendor user
vendor = User.objects.create(role=Roles.VENDOR, username='vendor1')

# Request as vendor to admin-only endpoint
view = VendorViewSet.as_view({'get': 'list'})
request = factory.get('/api/vendors/')
force_authenticate(request, user=vendor)
response = view(request)

# Should be 403
assert response.status_code == status.HTTP_403_FORBIDDEN
```

---

## Debugging Permission Issues

### 1. Check what permission class is being used
```python
# In your view class
print(self.permission_classes)  # Shows applied classes
```

### 2. Check user's role
```python
from permissions.rbac_policy import RBACPolicyHelper

role = RBACPolicyHelper.get_user_role(request.user)
print(f"User role: {role}")
```

### 3. Check if action is allowed
```python
from permissions.rbac_policy import WorkflowActionPermission, WorkflowAction

allowed = WorkflowActionPermission.check_action(
    request.user, 
    WorkflowAction.ASSESSMENT_SUBMIT
)
print(f"Can submit: {allowed}")
```

### 4. Check tenant mismatch
```python
# In TenantAwareQueryGuardMixin
print(f"User org: {self.get_tenant_value()}")
print(f"Object org: {getattr(obj, 'org', 'NOT SET')}")
```

---

## Common Issues & Solutions

### Issue: 403 Forbidden on endpoint that should work

**Debug steps:**
1. Check user has correct role: `print(RBACPolicyHelper.get_user_role(request.user))`
2. Check permission_classes on view: `print(view.permission_classes)`
3. Check workflow action matrix for that action
4. Check if object access is the issue (cross-tenant): `print(user.org vs object.org)`

### Issue: User can access resource from different organization

**Solution:** Ensure ViewSet has:
```python
from permissions.tenant_guard import TenantAwareQueryGuardMixin

class MyViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    tenant_filter_field = 'org'  # Match your model's org field
```

### Issue: Permission check works in one action but not another

**Solution:** Ensure both action method AND perform_X method have checks:
```python
def perform_create(self, serializer):
    # Check here for create
    WorkflowActionPermission.check_action_or_raise(...)
    
@action(detail=True, methods=["post"])
def custom_action(self, request, pk=None):
    # Check here for custom action
    WorkflowActionPermission.check_action_or_raise(...)
```

---

## Files at a Glance

| File | Purpose |
|------|---------|
| `permissions/rbac_policy.py` | Central policy matrix, permission classes, helper functions |
| `permissions/rbac.py` | Re-exports from rbac_policy for easier imports |
| `permissions/constants.py` | Role constants (ADMIN, REVIEWER, VENDOR) |
| `permissions/tenant_guard.py` | Tenant isolation mixins |
| `accounts/permissions.py` | App-specific permission class |
| `vendors/permissions.py` | Vendor creation permission |

---

## Import Cheat Sheet

```python
# Permission classes
from permissions.rbac_policy import (
    IsAdmin,
    IsReviewer,
    IsVendor,
    IsAdminOrReviewer,
    IsAuthenticated,
    WorkflowActionPermission,
)

# Role and action enums
from permissions.rbac_policy import (
    RoleType,
    WorkflowAction,
    RBACPolicyHelper,
)

# Constants
from permissions.constants import Roles

# Tenant guard
from permissions.tenant_guard import TenantAwareQueryGuardMixin
```

---

**Need help? Check RBAC_IMPLEMENTATION_SUMMARY.md for full details.**
