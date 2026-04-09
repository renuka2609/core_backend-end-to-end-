# RBAC System Architecture - Visual Guide

**Purpose:** Visual representation of the RBAC system design  
**Created:** April 4, 2026

---

## Permission Flow Diagram

### Request Processing Pipeline

```
HTTP Request
    ↓
[1] Is User Authenticated?
    ├─ NO → 401 Unauthorized
    ↓ YES
[2] Permission Classes Check (Class-Level)
    ├─ permission_classes = [IsAdmin, IsReviewer, etc.]
    ├─ NO → 403 Forbidden
    ↓ YES
[3] Tenant Guard Validation (Mixin)
    ├─ TenantAwareQueryGuardMixin.get_queryset()
    ├─ Filters by user.org
    ├─ NO → 403 Permission Denied
    ↓ YES
[4] Get Object (if detail request)
    ├─ _verify_object_belongs_to_tenant()
    ├─ NO → 404 Not Found / 403 Forbidden
    ↓ YES
[5] Execute View Logic
    ├─ perform_create(), @action, etc.
    ↓
[6] Workflow Action Check (Action-Level)
    ├─ WorkflowActionPermission.check_action_or_raise()
    ├─ Checks RBAC_POLICY_MATRIX
    ├─ NO → 403 Permission Denied
    ↓ YES
[7] Execute Business Logic
    ↓
[8] Log to Audit Trail
    ↓
200 Success Response
```

---

## Role Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                   User Roles                             │
└─────────────────────────────────────────────────────────┘
         │
    ┌────┼────┬───────────────┐
    │    │    │               │
    ↓    ↓    ↓               ↓
 ADMIN  REVIEWER  VENDOR    VIEWER
    │      │        │        (Fallback)
    │      │        │
    ├──────┤        │
    │ Can  │        │
    │ Do   │        │
    │ Most │        │
    │Things│        │
    │      │        │
    ├──────┴────────┤
    │               │
ASSESSMENT REVIEW ASSESSMENT SUBMIT
CREATE    DECIDE  ONLY
UPDATE
APPROVE   RESPOND
REJECT    TO
REVIEW    REMEDIATIONS

    │      │        │
    └──────┴────────┘

All roles can:
  - VIEW their org's resources
  - CREATE evidence/responses
  - SUBMIT/RESPOND per their role
```

---

## RBAC Policy Matrix - Visual

```
┌────────────────────────────────────────────────────────────────────┐
│                  RBAC_POLICY_MATRIX                                 │
│          (WorkflowAction → Set[RoleType])                           │
└────────────────────────────────────────────────────────────────────┘

ASSESSMENTS:
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✗     │   ✓    │   ✗    │
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✓    │
│ EDIT             │    ✓     │    ✗     │   ✓    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✗    │   ✗    │
│ SUBMIT           │    ✗     │    ✗     │   ✓    │   ✗    │
│ REVIEW           │    ✓     │    ✓     │   ✗    │   ✗    │
│ APPROVE/REJECT   │    ✓     │    ✓     │   ✗    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

REVIEWS:
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✓     │   ✗    │   ✗    │
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✗    │
│ EDIT             │    ✓     │    ✓     │   ✗    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✗    │   ✗    │
│ DECIDE           │    ✓     │    ✓     │   ✗    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

EVIDENCE:
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✗     │   ✓    │   ✗    │
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✗    │
│ EDIT             │    ✓     │    ✗     │   ✓    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✓    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

RESPONSES:
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✗     │   ✓    │   ✗    │
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✗    │
│ EDIT             │    ✓     │    ✗     │   ✓    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✓    │   ✗    │
│ SUBMIT           │    ✗     │    ✗     │   ✓    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

REMEDIATIONS:
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✓     │   ✗    │   ✗    │
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✗    │
│ EDIT             │    ✓     │    ✓     │   ✗    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✗    │   ✗    │
│ RESPOND          │    ✗     │    ✗     │   ✓    │   ✗    │
│ CLOSE            │    ✓     │    ✓     │   ✗    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

TEMPLATES (Admin-Only):
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✗     │   ✗    │   ✗    │
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✗    │
│ EDIT             │    ✓     │    ✗     │   ✗    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✗    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

VENDORS (Admin-Only):
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ CREATE           │    ✓     │    ✗     │   ✗    │   ✗    │
│ VIEW             │    ✓     │    ✗     │   ✗    │   ✗    │
│ EDIT             │    ✓     │    ✗     │   ✗    │   ✗    │
│ DELETE           │    ✓     │    ✗     │   ✗    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘

DASHBOARD:
┌──────────────────┬──────────┬──────────┬────────┬────────┐
│ Action           │ ADMIN    │ REVIEWER │ VENDOR │ VIEWER │
├──────────────────┼──────────┼──────────┼────────┼────────┤
│ VIEW             │    ✓     │    ✓     │   ✓    │   ✗    │
│ STATS            │    ✓     │    ✓     │   ✗    │   ✗    │
└──────────────────┴──────────┴──────────┴────────┴────────┘
```

---

## Permission Class Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│           django.rest_framework.permissions             │
│                  BasePermission                          │
└─────────────────────────────────────────────────────────┘
                        ↑
        ┌───────────────┼───────────────┐
        │               │               │
        ↓               ↓               ↓
┌───────────────┐ ┌────────────┐ ┌──────────────┐
│ IsAuthenticated│ │  IsAdmin   │ │ IsReviewer   │
└───────────────┘ └────────────┘ └──────────────┘
                                          ↑
                                          │
        ┌───────────────┬─────────────────┘
        │               │
        ↓               ↓
┌──────────────┐ ┌──────────────────┐
│   IsVendor   │ │ IsAdminOrReviewer │
└──────────────┘ └──────────────────┘

┌──────────────────────────────────────────────────────┐
│           WorkflowActionPermission                     │
│    (Uses RBAC_POLICY_MATRIX for validation)           │
│    (Most flexible - per-action granularity)           │
└──────────────────────────────────────────────────────┘

App-Specific Classes:
┌──────────────────────────┐
│  IsAdminOrReadOnly       │
│  (accounts/permissions)  │
└──────────────────────────┘

┌──────────────────────────┐
│  CanCreateVendor         │
│  (vendors/permissions)   │
└──────────────────────────┘
```

---

## App Implementation Status Map

```
IMPLEMENTATION STATUS BY APP

┌─── Full Implementation ───┐
│                           │
├─────────────────────────┐ │
│ ASSESSMENTS             │ │
│ ✓ permission_classes    │ │
│ ✓ perform_* methods     │ │
│ ✓ Action checks         │ │
│ ✓ Tenant guard mixin    │ │
└─────────────────────────┘ │
                             │
├─────────────────────────┐ │
│ REVIEWS                 │ │
│ ✓ permission_classes    │ │
│ ✓ Action checks         │ │
│ ✓ Tenant guard mixin    │ │
└─────────────────────────┘ │
                             │
├─────────────────────────┐ │
│ VENDORS                 │ │
│ ✓ permission_classes    │ │
│ ✓ perform_create check  │ │
│ ✓ Tenant guard mixin    │ │
└─────────────────────────┘ │
│                           │
└───────────────────────────┘

┌─── Partial Implementation ───┐
│                               │
├─────────────────────────────┐ │
│ TEMPLATES                   │ │
│ ✓ permission_classes        │ │
│ ✗ No action checks          │ │
│ ✓ Tenant guard mixin        │ │
│ FIX: Add perform_* checks   │ │
└─────────────────────────────┘ │
                                 │
├─────────────────────────────┐ │
│ RESPONSES                   │ │
│ ✓ permission_classes        │ │
│ ✗ No action checks          │ │
│ ✓ Tenant guard mixin        │ │
│ FIX: Add perform_* checks   │ │
└─────────────────────────────┘ │
                                 │
├─────────────────────────────┐ │
│ EVIDENCE                    │ │
│ ✓ permission_classes        │ │
│ ✗ No action checks          │ │
│ ✓ Tenant guard mixin        │ │
│ FIX: Add perform_* checks   │ │
└─────────────────────────────┘ │
                                 │
├─────────────────────────────┐ │
│ AUDIT                       │ │
│ ✓ permission_classes        │ │
│ ✗ No tenant isolation       │ │
│ ✗ No tenant guard mixin     │ │
│ FIX: Add mixin + filtering  │ │
└─────────────────────────────┘ │
                                 │
├─────────────────────────────┐ │
│ DASHBOARD                   │ │
│ ✓ permission_classes        │ │
│ ✗ No role-based filtering   │ │
│ FIX: Add action checks      │ │
└─────────────────────────────┘ │
│                               │
└───────────────────────────────┘

┌─── Critical Gaps ───┐
│                     │
├─────────────────────┐ │
│ REMEDIATIONS       │ │ ← 🔴 CRITICAL ISSUE
│ ✗ NO permissions   │ │
│ ✗ NO action checks  │ │ FIX: Add everything
│ ✓ Tenant mixin OK   │ │ Priority: P0
└─────────────────────┘ │
│                     │
└─────────────────────┘
```

---

## Tenant Isolation Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Organization (Tenant) Isolation               │
└─────────────────────────────────────────────────────────┘

Multiple Organizations (Separate Databases/Tables):

┌──────────────────┐        ┌──────────────────┐
│   Organization 1 │        │   Organization 2 │
├──────────────────┤        ├──────────────────┤
│ Users:           │        │ Users:           │
│ - Admin1         │        │ - AdminB         │
│ - Vendor1        │        │ - ReviewerB      │
│ - Reviewer1      │        │ - Vendor2        │
│                  │        │                  │
│ Assessments:     │        │ Assessments:     │
│ - Assessment 101 │        │ - Assessment 201 │
│ - Assessment 102 │        │ - Assessment 202 │
│                  │        │                  │
│ Reviews:         │        │ Reviews:         │
│ - Review 1       │        │ - Review 10      │
│ - Review 2       │        │ - Review 11      │
└──────────────────┘        └──────────────────┘

Request Flow for User1 (Org1):
    ↓ user.org = Org1
    ↓ TenantAwareQueryGuardMixin.get_tenant_value()
    ↓ Returns: Org1
    ↓ queryset.filter(org=Org1)  ← Only Org1 data
    ↓ Cannot access Assessment 201 (Org2)
    ↓ Cannot access Review 10 (Org2)
    ✓ Can only access Org1's resources
```

---

## Data Flow: Creating an Assessment

```
Request: POST /api/assessments/
Body: {name: "Assessment 1", ...}
Headers: Authorization: Bearer <token>
    │
    ↓
[1] Authentication Check
    ├─ Is token valid?
    ├─ Is user in database?
    ✓ YES → Continue
    │
    ↓
[2] Class Permission Check
    ├─ permission_classes = [IsAuthenticated]
    ├─ IsAuthenticated.has_permission()
    ✓ YES → Continue
    │
    ↓
[3] AssessmentViewSet.perform_create()
    ├─ WorkflowActionPermission.check_action_or_raise(
    │    user=user,
    │    action=WorkflowAction.ASSESSMENT_CREATE
    │ )
    ├─ RBACPolicyHelper.get_user_role(user)
    │    → Returns: RoleType.VENDOR
    ├─ Check RBAC_POLICY_MATRIX[ASSESSMENT_CREATE]
    │    → {RoleType.ADMIN, RoleType.VENDOR}
    ├─ VENDOR in allowed_roles?
    ✓ YES → Continue
    │
    ↓
[4] Create Assessment
    ├─ serializer.save(org=user.org)
    ├─ New Assessment created with org=Org1
    │
    ↓
[5] Log Audit Event
    ├─ AuditEvent created with:
    │    - user_id = VendorUser1
    │    - action = "assessment_created"
    │    - resource_id = Assessment.id
    │    - org = Org1
    │
    ↓
Response: 201 Created
{
    "id": 123,
    "name": "Assessment 1",
    "org": 1,
    "created_by": VendorUser1,
    ...
}
```

---

## Security Breach Scenarios (Current)

### Scenario 1: Different Role ❌ (FIXED)

```
Request: POST /api/templates/
User: VENDOR
    ↓
[1] Authentication ✓
[2] IsAuthenticated ✓
[3] Templates.perform_create()
    ├─ Has check? YES (in assessments, reviews, vendors)
    ├─ Can VENDOR create templates?
    ├─ Policy says: {RoleType.ADMIN} only
    ❌ DENIED (P1 fix needed - currently missing)
    │
Status: VULNERABLE (need to add check)
```

### Scenario 2: Different Organization ✅ (PROTECTED)

```
Request: GET /api/assessments/201/  (Assessment from Org2)
User: Org1/Admin1
    ↓
[1] Authentication ✓
[2] Permission ✓
[3] Tenant Guard: get_object()
    ├─ Get Org1 value from user
    ├─ Verify Assessment.org == Org1
    ├─ Assessment.org == Org2
    ✗ FAIL
    │
Status: ✅ PROTECTED - Returns 403 Forbidden
```

### Scenario 3: Unauthenticated User ✅ (PROTECTED)

```
Request: GET /api/assessments/
Headers: (no Authorization)
    ↓
[1] Authentication
    ├─ Is user authenticated?
    ❌ NO
    │
Status: ✅ PROTECTED - Returns 401 Unauthorized
```

### Scenario 4: Remediations - Anyone ❌ (CRITICAL)

```
Request: GET /api/remediations/
No auth check at all
    ↓
[1] Authentication
    ├─ Is there a permission_classes check?
    ❌ NO!
    │
[2] Direct database query
    ├─ Returns ALL remediations
    ├─ Cross-org data leak!
    │
Status: 🔴 CRITICAL VULNERABILITY
```

---

## Remediation Effort Map

```
Time to Fix by Priority Level:

P0 - CRITICAL (Fix This Week)
└─ Remediations
   ├─ Add permission_classes = [IsAuthenticated]    (5 min)
   ├─ Add perform_create check                      (5 min)
   ├─ Add respond() check                           (5 min)
   ├─ Add close() check                             (5 min)
   └─ Total: 20 minutes

P1 - HIGH PRIORITY (Next Sprint)
├─ Templates
│  ├─ Add perform_create check                      (20 min)
│  ├─ Add perform_update check                      (15 min)
│  └─ Add perform_destroy check                     (15 min)
│  → Subtotal: 50 minutes
│
├─ Responses
│  ├─ Add perform_create check                      (30 min)
│  ├─ Add perform_update check                      (20 min)
│  ├─ Add perform_destroy check                     (20 min)
│  ├─ Add submit() action check                     (20 min)
│  → Subtotal: 90 minutes
│
└─ Evidence
   ├─ Add perform_create check                      (30 min)
   ├─ Add perform_update check                      (20 min)
   └─ Add perform_destroy check                     (20 min)
   → Subtotal: 70 minutes

P1 Total: ~3.5 hours

P2 - MEDIUM PRIORITY (Q2 Planning)
├─ Dashboard
│  ├─ Add DASHBOARD_STATS check                     (45 min)
│  └─ Add DASHBOARD_VIEW check                      (15 min)
│  → Subtotal: 60 minutes
│
└─ Audit
   ├─ Add TenantAwareQueryGuardMixin                (30 min)
   ├─ Update get_queryset()                         (20 min)
   └─ Update custom actions                         (10 min)
   → Subtotal: 60 minutes

P2 Total: ~2 hours

GRAND TOTAL: 5.5 - 6 hours (+ testing)
```

---

## Testing Coverage Map

```
Current Test Coverage:

✅ Assessments
   ├─ Test create (vendor access)
   ├─ Test submit (vendor only)
   ├─ Test review (admin/reviewer only)
   └─ Test approve (admin only)

✅ Reviews
   ├─ Test create (reviewer access)
   └─ Test decision (reviewer access)

✅ Vendors
   ├─ Test create (admin only)
   └─ Test list (admin only)

⚠️ Responses
   ├─ Structure exists
   ├─ Missing: create role check test
   ├─ Missing: submit role check test
   └─ Missing: cross-org denial test

⚠️ Evidence
   ├─ Structure exists
   ├─ Missing: role check tests
   └─ Missing: cross-org denial test

⚠️ Templates
   ├─ Structure exists
   ├─ Missing: role check tests
   └─ Missing: vendor denial test

🔴 Remediations
   ├─ No tests exist
   ├─ Need: auth check test
   ├─ Need: role check tests
   └─ Need: cross-org denial test

Testing Needed: ~10-15 new test cases
```

---

## Summary Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    RBAC Implementation Status                │
└─────────────────────────────────────────────────────────────┘

Files to Review:
├─ permissions/rbac_policy.py       ← Central policy (26 KB)
├─ permissions/rbac.py              ← Re-exports (1 KB)
├─ permissions/constants.py         ← Role constants (1 KB)
├─ permissions/tenant_guard.py      ← Tenant isolation (6 KB)
│
├─ assessments/views.py             ← ✅ Full impl
├─ reviews/views.py                 ← ✅ Full impl
├─ vendors/views.py                 ← ✅ Full impl
├─ templates/views.py               ← ⚠️ Partial
├─ responses/views.py               ← ⚠️ Partial
├─ evidence/views.py                ← ⚠️ Partial
├─ remediations/views.py            ← 🔴 Critical gap
├─ audit/views.py                   ← ⚠️ Partial
├─ dashboard/views.py               ← ⚠️ Partial
└─ accounts/views.py                ← ✅ Auth only

Implementation: 30% Complete → 100% Target in 6 hours
Tests: 30% Complete → 80% Target in 8-10 hours
Documentation: 100% Complete (4 reference docs)

Next Action: Review RBAC_ISSUES_AND_ACTION_ITEMS.md for fixes
```

---

**End of Visual Architecture Guide**
