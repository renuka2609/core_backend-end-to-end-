# P0-Ready Environment Setup for QA

## Quick Start (5 minutes)

### 1. Activate Virtual Environment
```powershell
cd "d:\AIDS\internship\core_backend(end to end)"
.\.venv\Scripts\activate.ps1
```

### 2. Run Database Setup & Seed
```powershell
python seed_p0_ready.py
```

Expected output:
```
================================================================================
✅ SETUP COMPLETE - Database ready for P0 validation
================================================================================
```

### 3. Start Development Server
```powershell
python manage.py runserver
```

Expected output:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## Environment Configuration

### Database
- **Type:** SQLite (db.sqlite3)
- **Location:** `d:\AIDS\internship\core_backend(end to end)\db.sqlite3`
- **Schema:** Auto-created by Django migrations

### Django Settings
- **DEBUG:** True (development mode)
- **SECRET_KEY:** django-insecure-change-this-key
- **ALLOWED_HOSTS:** ['*', 'testserver']
- **TIME_ZONE:** Asia/Kolkata
- **INSTALLED_APPS:** All P0 apps are enabled

### REST Framework Configuration
```python
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}
```

**Key:** Custom exception handler ensures all 5xx errors return JSON instead of HTML debug pages.

---

## Test Users (After Running seed_p0_ready.py)

### Admin User
- **Username:** test_admin
- **Email:** admin@test.com
- **Password:** TestPass123!
- **Role:** ADMIN
- **Permissions:** Create templates, vendors, approve assessments

### Vendor User
- **Username:** test_vendor
- **Email:** vendor@test.com
- **Password:** TestPass123!
- **Role:** VENDOR
- **Permissions:** Submit assessments, upload evidence/responses

### Reviewer User
- **Username:** test_reviewer
- **Email:** reviewer@test.com
- **Password:** TestPass123!
- **Role:** REVIEWER
- **Permissions:** Review assessments, make review decisions

---

## Test Data (After Running seed_p0_ready.py)

### Organization
- **Name:** Test Organization 1
- **ID:** 1 (typically)

### Vendors
1. Acme Corp
2. Tech Solutions Inc
3. Global Services Ltd

### Templates
1. Compliance Assessment Template (v1)
   - Section: Security Controls
   - Questions: 3 sample questions included

### Assessments
- Status: ASSIGNED (ready for vendor submission)
- Linked to first 2 vendors

---

## Key Fixes in P0-Ready Build

### 1. Vendor Create (500 → 201)
**Issue:** Vendor creation was failing with 500 errors

**Fix:**
- `org` field is now read-only in VendorSerializer
- `org` is auto-attached from request.user.org in perform_create
- Client no longer needs to send `org` in POST payload

**Test:**
```bash
POST /api/vendors/vendors/
Headers: Authorization: Bearer <token>
Body: {"name": "New Vendor Corp"}
Expected: 201 with org auto-populated
```

### 2. JSON Error Responses
**Issue:** Debug HTML pages on 500 errors

**Fix:**
- Custom exception handler in `config/exceptions.py`
- All unhandled exceptions return JSON
- Format: `{"detail": "...", "error": "..."}`

**Verification:** All 500 errors now return JSON

### 3. Permission Classes
**Issue:** Hardcoded role checks scattered throughout views

**Fix:**
- New permission classes in `permissions/rbac.py`:
  - `CanCreateTemplate` - Admin only
  - `CanCreateTemplateVersion` - Admin only
  - `CanSubmitAssessment` - Vendor only
  - `CanReviewAssessment` - Reviewer/Admin
  - `CanApproveAssessment` - Admin only
- Applied to all views
- Removes inline role checks

### 4. 409 Conflict for Invalid Transitions
**Issue:** State transitions not validated uniformly

**Fix:**
- Assessment.can_transition_to() validates all state changes
- All endpoints return 409 for invalid transitions:
  - submit: ASSIGNED → SUBMITTED only
  - review: SUBMITTED → REVIEWED only
  - approve: REVIEWED → APPROVED only

**Test:**
```bash
# Try to submit an already-submitted assessment
POST /api/assessments/assessments/{id}/submit/
Expected: 409 with error message
```

### 5. Audit Logging
**Issue:** Missing audit trails for critical write actions

**Fix:** Comprehensive audit logging added:
- **Vendor:** vendor_created, vendor_updated
- **Template:** create_template, create_template_version
- **Assessment:** create_assessment, submit_assessment, review_assessment, approve_assessment
- **Response:** response_created, response_updated, response_submitted
- **Evidence:** evidence_created, evidence_updated, evidence_deleted
- **Review:** create_review, make_review_decision
- **Remediation:** remediation_created, remediation_responded, remediation_closed

**Verify:**
```bash
GET /api/audit/audit-logs/?org_id=1
Returns all logged actions with timestamps and metadata
```

---

## Validation Checklist

### Permission Tests ✅
- [ ] Admin can create vendors
- [ ] Vendor cannot create vendors (403)
- [ ] Admin can create templates
- [ ] Non-admin cannot create templates (403)
- [ ] Vendor can submit assessments
- [ ] Non-vendor cannot submit (403)
- [ ] Reviewer can review assessments
- [ ] Vendor cannot review (403)
- [ ] Admin can approve assessments
- [ ] Non-admin cannot approve (403)

### State Transition Tests ✅
- [ ] Submit new assessment (ASSIGNED → SUBMITTED) = 200
- [ ] Submit already-submitted assessment = 409
- [ ] Review submitted assessment (SUBMITTED → REVIEWED) = 200
- [ ] Review non-submitted assessment = 409
- [ ] Approve reviewed assessment (REVIEWED → APPROVED) = 200
- [ ] Approve non-reviewed assessment = 409

### Org Linkage Tests ✅
- [ ] Vendor POST includes no org field, still receives org
- [ ] Assessment auto-links to user org
- [ ] Template auto-links to user org
- [ ] Users only see data from their org

### Error Handling Tests ✅
- [ ] Invalid transition returns 409 JSON (not HTML)
- [ ] Permission denied returns 403 JSON (not HTML)
- [ ] Missing required fields returns 400 JSON (not HTML)
- [ ] No 500 errors occur during normal workflow
- [ ] All errors return proper JSON format

### Audit Logging Tests ✅
- [ ] Create vendor → audit log recorded
- [ ] Create assessment → audit log recorded
- [ ] Submit assessment → audit log recorded
- [ ] Review assessment → audit log recorded
- [ ] Approve assessment → audit log recorded
- [ ] Create review → audit log recorded
- [ ] Make review decision → audit log recorded

---

## Troubleshooting

### Virtual Environment Issues
```powershell
# If Python not found, activate venv first
.\.venv\Scripts\activate.ps1

# If packages missing
pip install -r requirements.txt
```

### Database Issues
```powershell
# Reset database (careful - deletes all data)
rm db.sqlite3
python manage.py migrate
python seed_p0_ready.py
```

### Port Already in Use
```powershell
# Run on different port
python manage.py runserver 8001
```

### Import Errors
```powershell
# Ensure you're using venv Python
which python  # Should show .venv path

# Reinstall packages if needed
pip install -r requirements.txt --force-reinstall
```

---

## Files Modified for P0-Ready

1. **vendors/serializers.py**
   - Made `org` read-only

2. **config/exceptions.py**
   - New custom exception handler

3. **config/settings.py**
   - Added EXCEPTION_HANDLER configuration

4. **permissions/rbac.py**
   - Added new permission classes

5. **templates/views.py**
   - Applied CanCreateTemplate permission class
   - Removed inline role checks

6. **assessments/views.py**
   - Applied permission classes
   - Removed inline role checks

7. **reviews/views.py**
   - Applied IsAdminOrReviewer permission class
   - Removed inline role checks

8. **responses/views.py**
   - Added audit logging
   - Added org-scoped queryset

9. **evidence/views.py**
   - Added audit logging
   - Added org-scoped queryset

10. **seed_p0_ready.py** (new)
    - Complete setup and seed script

---

## Next Steps After Validation

If all tests pass:

1. **Commit to git:**
   ```powershell
   git add -A
   git commit -m "P0-ready: Fix vendor create 500, enforce permissions, add audit logging"
   git tag -a p0-ready -m "P0 conformance ready for QA validation"
   ```

2. **Push to repository:**
   ```powershell
   git push origin main
   git push origin p0-ready
   ```

3. **Document in release notes:**
   - List all fixes applied
   - Include reproduction steps
   - Provide test checklist

---

## Support

**Questions or Issues?**
- Check error logs: `tail -f error.log` (if configured)
- Review audit logs: `/api/audit/audit-logs/`
- Check Django debug toolbar (if enabled)
- Review recent changes: `git log --oneline -10`
