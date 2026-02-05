# Review Module - P0 Conformance Fixes

## Summary
Fixed critical issues in the Review module to ensure P0 conformance with the Assessment workflow. The module now properly implements org linkage, audit logging, RBAC, and state transitions.

## Issues Fixed

### 1. **Model Schema Issue: Duplicate Org Fields**
**Problem:**
- Review model had conflicting org representation:
  - `org_id = models.IntegerField()` (legacy/incorrect)
  - `org = models.ForeignKey(Organization)` (correct, but duplicated)

**Solution:**
- Removed `org_id` IntegerField entirely
- Kept `org` ForeignKey as single source of truth
- Made it nullable for flexibility: `org = ForeignKey(Organization, on_delete=CASCADE, null=True, blank=True)`
- Fixed import to use `orgs.models.Organization` (not `accounts.models`)

**Files Changed:**
- `reviews/models.py` - Removed org_id field, fixed imports, added updated_at

**Migration:**
```bash
Created: reviews/migrations/0002_alter_review_options_remove_review_org_id_review_org_and_more.py
```

---

### 2. **Views: Incorrect Org Assignment & log_event() Calls**
**Problem:**
- `perform_create()` used `org_id=self.request.user.org_id` (legacy pattern)
- `log_event()` calls passed `obj=review` instead of `object_id=review.id`
- Missing import of `Roles` constants
- Missing `IsAuthenticated` permission class

**Solution:**
- Changed `org_id=...` to `org=self.request.user.org` in perform_create()
- Fixed all `log_event()` calls to use correct signature: `object_id=review.id, metadata={...}`
- Added proper Roles import from `permissions.constants`
- Added `permission_classes = [IsAuthenticated]` to ViewSet
- Enhanced decision() method with proper metadata logging

**Files Changed:**
- `reviews/views.py`:
  - Removed `services.scoring_client.trigger_scoring` import (unused)
  - Added imports: `IsAuthenticated`, `Roles`, proper `log_event()` usage
  - Fixed `get_queryset()` to use `org=` instead of `org_id=`
  - Fixed `perform_create()` org assignment and log_event() call
  - Enhanced `decision()` endpoint with metadata and RBAC check

---

### 3. **Serializer: Incorrect Read-Only Fields**
**Problem:**
- Serializer used `read_only_fields = ['reviewer', 'org_id', 'decision']`
- Referenced non-existent `org_id` field in read_only_fields
- Used `__all__` which exposed internal fields

**Solution:**
- Changed to explicit fields list
- Updated read_only_fields to use `org` (FK) instead of `org_id`
- Properly structured: `['id', 'org', 'assessment', 'reviewer', 'comments', 'decision', 'created_at', 'updated_at']`

**Files Changed:**
- `reviews/serializers.py` - Fixed fields and read_only_fields

---

### 4. **Seed Script: Missing Reviewer User**
**Problem:**
- Seed script only created admin and vendor users
- No reviewer user available for testing workflow

**Solution:**
- Added reviewer user creation to seed.py with role=Roles.REVIEWER

**Files Changed:**
- `users/management/commands/seed.py` - Added reviewer user creation

---

## P0 Conformance Validation

### ✅ RBAC Consistency
- Review model uses centralized `Roles` constants
- ReviewViewSet enforces `IsAuthenticated` permission
- Decision endpoint checks `if request.user.role not in [Roles.REVIEWER, Roles.ADMIN]`

### ✅ 409 Conflict for Invalid Transitions
- Decision endpoint returns 409 Conflict when:
  - Review already has a decision (not 'pending')
  - Attempting to change final decision

```python
if review.decision != "pending":
    return Response(
        {"detail": "review already decided"},
        status=status.HTTP_409_CONFLICT
    )
```

### ✅ Audit Logging for All Critical Actions
- `create_review` action logged with metadata: `{assessment_id}`
- `make_review_decision` action logged with metadata: `{assessment_id, previous_decision, new_decision}`
- All logs include org context from user

### ✅ Org Linkage Guaranteed
- Review creation always sets `org=self.request.user.org`
- No 500 errors from missing org
- Org is always populated in audit logs

---

## API Endpoints

### Create Review
```
POST /api/reviews/
Content-Type: application/json
Authorization: Bearer <token>

{
  "assessment": <id>,
  "comments": "Review text"
}

Response (201):
{
  "id": 1,
  "org": 1,
  "assessment": 1,
  "reviewer": 3,
  "comments": "Review text",
  "decision": "pending",
  "created_at": "2026-02-04T15:57:48.921145+05:30",
  "updated_at": "2026-02-04T15:57:48.921168+05:30"
}
```

### Make Review Decision
```
POST /api/reviews/{id}/decision/
Content-Type: application/json
Authorization: Bearer <token>

{
  "decision": "approved"  // or "rejected"
}

Response (200):
{
  "status": "approved"
}

Response (409 - already decided):
{
  "detail": "review already decided"
}

Response (403 - unauthorized):
{
  "detail": "Only reviewers/admins can make review decisions"
}
```

---

## Test Results

All P0 conformance tests passing:

```
[TEST 1] Review Model Structure ✅
  - Has org (ForeignKey to Organization)
  - Does NOT have org_id (IntegerField)
  - Has updated_at (DateTimeField)

[TEST 2] Review Creation - Org Linkage ✅
  - Review created with org matching reviewer's org
  - No 500 errors from missing org

[TEST 3] Audit Logging for Review Actions ✅
  - create_review logged with org context
  - Metadata includes assessment_id

[TEST 4] Review Decision - 409 Conflict ✅
  - First decision: 200 OK
  - Duplicate decision: 409 Conflict

[TEST 5] Audit Logging for Decision ✅
  - make_review_decision logged with full metadata
  - Tracks previous and new decision states

[TEST 6] RBAC Enforcement ✅
  - Vendors get 403 Forbidden
  - Only Reviewers/Admins can decide
```

---

## Files Modified

1. `reviews/models.py` - Fixed model schema
2. `reviews/views.py` - Fixed views, imports, and log_event calls
3. `reviews/serializers.py` - Fixed fields and read_only_fields
4. `users/management/commands/seed.py` - Added reviewer user
5. `reviews/migrations/0002_*` - Created migration for schema changes

---

## Database Migration

```bash
$ python manage.py makemigrations reviews
Migrations for 'reviews':
  reviews\migrations\0002_alter_review_options_remove_review_org_id_review_org_and_more.py
    ~ Change Meta options on review
    - Remove field org_id from review
    + Add field org to review
    + Add field updated_at to review
    ~ Alter field comments on review

$ python manage.py migrate reviews
Applying reviews.0002_alter_review_options_remove_review_org_id_review_org_and_more... OK
```

---

## Impact

These fixes ensure the Review module is fully consistent with:
- Assessment workflow state machine
- Templates org linkage patterns
- Centralized RBAC approach
- Comprehensive audit trail for compliance

The module can now be safely integrated into the end-to-end assessment workflow without 500 errors or missing audit trails.
