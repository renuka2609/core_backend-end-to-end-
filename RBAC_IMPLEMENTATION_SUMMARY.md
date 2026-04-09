# RBAC Implementation - Comprehensive Summary

**Generated:** April 4, 2026  
**System:** VRM Backend (Django)

---

## Table of Contents
1. [Permission Classes](#permission-classes)
2. [Role Definitions](#role-definitions)
3. [Workflow Actions & RBAC Policy Matrix](#workflow-actions--rbac-policy-matrix)
4. [Implementation by App](#implementation-by-app)
5. [Duplicate Checks Analysis](#duplicate-checks-analysis)
6. [Missing/Incomplete Implementations](#missingincomplete-implementations)
7. [Architecture Overview](#architecture-overview)

---

## Permission Classes

### Core Permission Classes (Central Design)

All permission classes are defined in **`permissions/rbac_policy.py`** and re-exported via **`permissions/rbac.py`**.

| Class Name | Location | Purpose | Allowed Roles |
|-----------|----------|---------|----------------|
| `IsAuthenticated` | `rbac_policy.py` | Requires any authenticated user | Any logged-in user |
| `IsAdmin` | `rbac_policy.py` | Admin-only access | ADMIN |
| `IsReviewer` | `rbac_policy.py` | Reviewer and Admin access | ADMIN, REVIEWER |
| `IsVendor` | `rbac_policy.py` | Vendor-only access | VENDOR |
| `IsAdminOrReviewer` | `rbac_policy.py` | Admin or Reviewer access | ADMIN, REVIEWER |
| `WorkflowActionPermission` | `rbac_policy.py` | Policy matrix-based action validation | Configurable per action |

### App-Specific Permission Classes

| Class Name | Location | Purpose | Allowed Roles |
|-----------|----------|---------|----------------|
| `IsAdminOrReadOnly` | `accounts/permissions.py` | Admin can modify; others read-only | Authenticated users (read), ADMIN (write) |
| `CanCreateVendor` | `vendors/permissions.py` | Vendor creation restricted | ADMIN, REVIEWER |

---

## Role Definitions

### Roles Defined in `permissions/constants.py`

```python
class Roles:
    ADMIN = "admin"
    REVIEWER = "reviewer"
    VENDOR = "vendor"
    
    CHOICES = [
        (ADMIN, "Admin"),
        (REVIEWER, "Reviewer"),
        (VENDOR, "Vendor"),
    ]
    
    ALL_ROLES = [ADMIN, REVIEWER, VENDOR]
```

### Role Resolution (RBACPolicyHelper)

The system uses **multi-strategy role resolution** to handle legacy data and different role storage methods:

1. **Superuser** → Maps to `ADMIN`
2. **User.role attribute** → Direct role field
3. **User.groups** → Group-based roles
4. **Default** → Falls back to `VIEWER`

**Location:** `permissions/rbac_policy.py`, `RBACPolicyHelper.get_user_role()`

---

## Workflow Actions & RBAC Policy Matrix

### Central RBAC Policy Matrix

The system defines a **central policy matrix** that maps each `WorkflowAction` to allowed roles.

**Location:** `permissions/rbac_policy.py`, `RBAC_POLICY_MATRIX`

### Workflow Actions by Domain

#### Assessment Workflow (8 actions)
```
ASSESSMENT_CREATE     → {ADMIN, VENDOR}
ASSESSMENT_VIEW       → {ADMIN, REVIEWER, VENDOR, VIEWER}
ASSESSMENT_EDIT       → {ADMIN, VENDOR}
ASSESSMENT_DELETE     → {ADMIN}
ASSESSMENT_SUBMIT     → {VENDOR}
ASSESSMENT_REVIEW     → {ADMIN, REVIEWER}
ASSESSMENT_APPROVE    → {ADMIN, REVIEWER}
ASSESSMENT_REJECT     → {ADMIN, REVIEWER}
```

#### Review Workflow (5 actions)
```
REVIEW_CREATE    → {ADMIN, REVIEWER}
REVIEW_VIEW      → {ADMIN, REVIEWER, VENDOR}
REVIEW_EDIT      → {ADMIN, REVIEWER}
REVIEW_DELETE    → {ADMIN}
REVIEW_DECIDE    → {ADMIN, REVIEWER}
```

#### Evidence Workflow (4 actions)
```
EVIDENCE_CREATE  → {ADMIN, VENDOR}
EVIDENCE_VIEW    → {ADMIN, REVIEWER, VENDOR}
EVIDENCE_EDIT    → {ADMIN, VENDOR}
EVIDENCE_DELETE  → {ADMIN, VENDOR}
```

#### Response Workflow (5 actions)
```
RESPONSE_CREATE  → {ADMIN, VENDOR}
RESPONSE_VIEW    → {ADMIN, REVIEWER, VENDOR}
RESPONSE_EDIT    → {ADMIN, VENDOR}
RESPONSE_DELETE  → {ADMIN, VENDOR}
RESPONSE_SUBMIT  → {VENDOR}
```

#### Remediation Workflow (6 actions)
```
REMEDIATION_CREATE   → {ADMIN, REVIEWER}
REMEDIATION_VIEW     → {ADMIN, REVIEWER, VENDOR}
REMEDIATION_EDIT     → {ADMIN, REVIEWER}
REMEDIATION_DELETE   → {ADMIN}
REMEDIATION_RESPOND  → {VENDOR}
REMEDIATION_CLOSE    → {ADMIN, REVIEWER}
```

#### Template Workflow (4 actions)
```
TEMPLATE_CREATE  → {ADMIN}
TEMPLATE_VIEW    → {ADMIN, REVIEWER, VENDOR}
TEMPLATE_EDIT    → {ADMIN}
TEMPLATE_DELETE  → {ADMIN}
```

#### Vendor Management (4 actions)
```
VENDOR_CREATE  → {ADMIN}
VENDOR_VIEW    → {ADMIN}
VENDOR_EDIT    → {ADMIN}
VENDOR_DELETE  → {ADMIN}
```

#### Dashboard (2 actions)
```
DASHBOARD_VIEW   → {ADMIN, REVIEWER, VENDOR}
DASHBOARD_STATS  → {ADMIN, REVIEWER}
```

---

## Implementation by App

### 1. **assessments/** 

**ViewSet:** `AssessmentViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | `IsAuthenticated` | `ASSESSMENT_CREATE` ✓ |
| Detail/Update | GET/PUT | `IsAuthenticated` | (implicit via list) |
| Delete | DELETE | `IsAuthenticated` | (implicit via list) |
| `submit` (action) | POST | `IsAuthenticated` | `ASSESSMENT_SUBMIT` ✓ |
| `review` (action) | POST | `IsAuthenticated` | `ASSESSMENT_REVIEW` ✓ |
| `approve` (action) | POST | `IsAuthenticated` | `ASSESSMENT_APPROVE` ✓ |
| `remediate` (action) | POST | `IsAuthenticated` | `ASSESSMENT_REVIEW` ✓ |

**Implementation Pattern:**
```python
def perform_create(self, serializer):
    WorkflowActionPermission.check_action_or_raise(
        self.request.user,
        WorkflowAction.ASSESSMENT_CREATE
    )
    serializer.save(org=self.request.user.org)

@action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
def submit(self, request, pk=None):
    WorkflowActionPermission.check_action_or_raise(
        request.user,
        WorkflowAction.ASSESSMENT_SUBMIT
    )
    # ... action logic
```

**Role-Based Access:**
- **VENDOR:** Create, Edit, Submit assessments
- **ADMIN/REVIEWER:** Review, Approve, Reject assessments
- **ALL:** View own org's assessments

---

### 2. **reviews/**

**ViewSet:** `ReviewViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`  
**Permission Classes:** `[IsAuthenticated, IsReviewer]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | `IsAuthenticated, IsReviewer` | (implicit) |
| Detail/Update | GET/PUT | `IsAuthenticated, IsReviewer` | (implicit) |
| Delete | DELETE | `IsAuthenticated, IsReviewer` | (implicit) |
| `decision` (action) | POST | `IsAuthenticated, IsReviewer` | `REVIEW_DECIDE` ✓ |

**Role-Based Access:**
- **ADMIN/REVIEWER:** Full access (all review operations)
- **OTHERS:** No access (filtered by permission_classes)

---

### 3. **vendors/**

**ViewSet:** `VendorViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`  
**Permission Classes:** `[IsAuthenticated, IsAdmin]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | `IsAuthenticated, IsAdmin` | `VENDOR_CREATE` ✓ |
| Detail/Update | GET/PUT | `IsAuthenticated, IsAdmin` | (implicit) |
| Delete | DELETE | `IsAuthenticated, IsAdmin` | (implicit) |

**Role-Based Access:**
- **ADMIN:** Full access (vendor management)
- **OTHERS:** No access (filtered by permission_classes)

---

### 4. **templates/**

**ViewSet:** `TemplateViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`  
**Permission Classes:** `[IsAuthenticated]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | `IsAuthenticated` | (no explicit check) |
| Detail/Update | GET/PUT | `IsAuthenticated` | (no explicit check) |
| Delete | DELETE | `IsAuthenticated` | (no explicit check) |

⚠️ **FINDING:** No `WorkflowActionPermission` checks implemented. Relies on `IsAuthenticated` only.

---

### 5. **responses/**

**ViewSet:** `ResponseViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`  
**Permission Classes:** `[IsAuthenticated]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | `IsAuthenticated` | (no explicit check) |
| Detail/Update | GET/PUT | `IsAuthenticated` | (no explicit check) |
| Delete | DELETE | `IsAuthenticated` | (no explicit check) |
| `submit` (action) | POST | (none) | (no check) |

⚠️ **FINDING:** No `WorkflowActionPermission` checks implemented.

---

### 6. **evidence/**

**ViewSet:** `EvidenceViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`  
**Permission Classes:** `[IsAuthenticated]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | `IsAuthenticated` | (no explicit check) |
| Detail/Update | GET/PUT | `IsAuthenticated` | (no explicit check) |
| Delete | DELETE | `IsAuthenticated` | (no explicit check) |

⚠️ **FINDING:** No `WorkflowActionPermission` checks implemented.

---

### 7. **remediations/**

**ViewSet:** `RemediationViewSet`  
**Base Mixin:** `TenantAwareQueryGuardMixin`  
**Permission Classes:** (none explicitly set)

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List/Create | GET/POST | (none) | (no explicit check) |
| Detail/Update | GET/PUT | (none) | (no explicit check) |
| Delete | DELETE | (none) | (no explicit check) |
| `respond` (action) | POST | (none) | (no check) |
| `close` (action) | POST | (none) | (no check) |

⚠️ **FINDING:** No permission classes or action checks implemented.

---

### 8. **audit/**

**ViewSet:** `AuditEventViewSet`  
**Type:** Read-only ViewSet  
**Permission Classes:** `[IsAuthenticated]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| List | GET | `IsAuthenticated` | (none) |
| Detail | GET | `IsAuthenticated` | (none) |
| `by_resource` (action) | GET | `IsAuthenticated` | (none) |
| `by_user` (action) | GET | `IsAuthenticated` | (none) |
| `by_date_range` (action) | GET | `IsAuthenticated` | (none) |

**Role-Based Access:**
- **ALL:** Full read-only access (all authenticated users see audit events)

---

### 9. **dashboard/**

**Views:** Two separate APIViews (not ViewSet)  
**Permission Classes:** `[IsAuthenticated]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| `DashboardStatsView` | GET | `IsAuthenticated` | (none) |
| `DashboardActivityFeedView` | GET | `IsAuthenticated` | (none) |

**Role-Based Access:**
- **ALL:** Access to own org's stats/feed (filtered by org in view logic)

---

### 10. **accounts/**

**Views:** Two separate APIViews (not ViewSet)  
**Permission Classes:**
- `LoginView`: `[AllowAny]`
- `LogoutView`: `[IsAuthenticated]`

| Endpoint | Method | Permission | Workflow Action Check |
|----------|--------|-----------|----------------------|
| `login` | POST | `AllowAny` | (none) |
| `logout` | POST | `IsAuthenticated` | (none) |

**Role-Based Access:**
- **NONE:** No role checks (authentication only)

---

## Duplicate Checks Analysis

### ✅ NO SIGNIFICANT DUPLICATES FOUND

**Why:** The system uses a **centralized pattern** with two approaches:

#### Approach 1: Class-Level Permission Classes (Most Views)
```python
permission_classes = [IsAuthenticated, IsAdmin]
# OR
permission_classes = [IsAuthenticated, IsReviewer]
```
- Simple, declarative
- Enforced at class level
- Cannot be action-specific
- Used in: Reviews, Vendors

#### Approach 2: Action-Level Workflow Checks (Some Views)
```python
@action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
def submit(self, request, pk=None):
    WorkflowActionPermission.check_action_or_raise(
        request.user,
        WorkflowAction.ASSESSMENT_SUBMIT
    )
```
- Flexible, action-specific
- Used in: Assessments, Reviews (decision action)

#### No Conflicts
Since each approach is used in different contexts, there are **no conflicting or duplicate permission checks**. Each is appropriate for its use case.

---

## Missing/Incomplete Implementations

### 🔴 CRITICAL GAPS

#### 1. **Templates ViewSet - No Workflow Checks**
- **File:** `templates/views.py`
- **Issue:** Only uses `IsAuthenticated`, no role validation
- **Impact:** Any authenticated user can create/edit/delete templates
- **Expected Behavior:** Should restrict to ADMIN only
- **Fix:** Add `WorkflowActionPermission` checks or use `permission_classes = [IsAuthenticated, IsAdmin]`

#### 2. **Responses ViewSet - No Workflow Checks**  
- **File:** `responses/views.py`
- **Issue:** Only uses `IsAuthenticated`, no validation for create/submit
- **Impact:** Any authenticated user can create/submit responses
- **Expected Behavior:** 
  - CREATE: ADMIN, VENDOR
  - SUBMIT: VENDOR only
  - VIEW/EDIT: ADMIN, REVIEWER, VENDOR
- **Fix:** Add `WorkflowActionPermission` checks in perform_create, submit action

#### 3. **Evidence ViewSet - No Workflow Checks**
- **File:** `evidence/views.py`
- **Issue:** Only uses `IsAuthenticated`, no role validation
- **Impact:** Any authenticated user can create/edit/delete evidence
- **Expected Behavior:**
  - CREATE/EDIT: ADMIN, VENDOR
  - VIEW: ADMIN, REVIEWER, VENDOR
  - DELETE: ADMIN, VENDOR
- **Fix:** Add `WorkflowActionPermission` checks

#### 4. **Remediations ViewSet - No Permission Classes**
- **File:** `remediations/views.py`
- **Issue:** No permission_classes defined at all + no workflow checks
- **Impact:** **HIGH SECURITY RISK** - Unauthenticated access possible
- **Expected Behavior:**
  - CREATE: ADMIN, REVIEWER
  - RESPOND: VENDOR only
  - CLOSE: ADMIN, REVIEWER
- **Fix:** 
  1. Add `permission_classes = [IsAuthenticated]`
  2. Add `TenantAwareQueryGuardMixin`
  3. Add `WorkflowActionPermission` checks for respond/close actions

---

### ⚠️ MODERATE GAPS

#### 5. **Dashboard - All Users See All Org Data**
- **File:** `dashboard/views.py`
- **Issue:** Views check only `IsAuthenticated`, no role-based stats filtering
- **Current:** DASHBOARD_VIEW and DASHBOARD_STATS in policy matrix define:
  - DASHBOARD_VIEW: {ADMIN, REVIEWER, VENDOR}
  - DASHBOARD_STATS: {ADMIN, REVIEWER}
- **But:** Views don't enforce these roles
- **Impact:** VENDOR users might see ADMIN-only stats
- **Fix:** Add role checks before returning stats

#### 6. **Audit - All Users See All Audit Events**
- **File:** `audit/views.py`
- **Issue:** Read-only access for all authenticated users
- **Current:** No tenant isolation on audit logs
- **Impact:** Users see logs from other organizations
- **Expected:** Should be filtered by user's org (with admin access to all orgs)
- **Fix:** Apply `TenantAwareQueryGuardMixin` or add custom filtering in `get_queryset()`

---

## Architecture Overview

### Permission Resolution Flow

```
Request → View Permission Classes
          ↓
       IsAuthenticated? (Base check)
          ↓ YES
       Apply Class-Level Permissions (IsAdmin, IsReviewer, etc.)
          ↓ PASSED
       Apply Tenant Guard Mixin (TenantAwareQueryGuardMixin)
          ↓ PASSED
       Execute Action
          ↓
       If Workflow Action → WorkflowActionPermission.check_action_or_raise()
          ↓ PASSED
       Execute Business Logic
```

### Multi-Layered Security

1. **Layer 1: Authentication** (`IsAuthenticated`)
   - Is the user logged in?

2. **Layer 2: Role-Based Access** (Permission Classes)
   - Does the user's role allow access to this endpoint?

3. **Layer 3: Tenant Isolation** (`TenantAwareQueryGuardMixin`)
   - Does the requested object belong to the user's organization?

4. **Layer 4: Workflow Validation** (`WorkflowActionPermission`)
   - Is this specific action allowed for this user in this context?

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Permission Classes** | 8 (5 core + 3 specialized) |
| **Roles** | 3 (Admin, Reviewer, Vendor) |
| **Workflow Actions** | 38 total actions |
| **ViewSets/Views** | 10 |
| **Apps with Full Implementation** | 3 (assessments, reviews, vendors) |
| **Apps with Partial Implementation** | 4 (templates, responses, evidence, dashboard) |
| **Apps with No Implementation** | 1 (remediations) |
| **Critical Issues** | 1 (remediations) |
| **High Priority Fixes** | 4 (templates, responses, evidence, dashboard) |

---

## Recommendations

### Immediate Actions (P0)
1. ✅ Fix **Remediations** - Add permission_classes and mixin
2. ✅ Implement workflow action checks in **Evidence, Responses, Templates**
3. ✅ Add tenant isolation to **Audit** logs
4. ✅ Add role filtering to **Dashboard** stats endpoints

### Code Quality Improvements (P1)
1. Consider creating a decorator `@require_workflow_action(WorkflowAction.XXX)` to reduce boilerplate
2. Document the permission matrix in each viewset's docstring
3. Add integration tests for each role in each app
4. Create admin action to audit permission assignments

### Documentation (P2)
1. Create per-app permission override guide
2. Add permission troubleshooting guide
3. Document how to add new workflow actions
4. Create audit trail analysis guide

---

**End of RBAC Implementation Summary**
