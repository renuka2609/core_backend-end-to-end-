# P0-Ready Quick Reference for QA

## One-Command Setup

```powershell
# Complete setup in one go
cd "d:\AIDS\internship\core_backend(end to end)"; .\.venv\Scripts\activate.ps1; python seed_p0_ready.py; python manage.py runserver
```

## Server Starting

```powershell
# Navigate to project
cd "d:\AIDS\internship\core_backend(end to end)"

# Activate environment
.\.venv\Scripts\activate.ps1

# Start server
python manage.py runserver

# Server will be at: http://127.0.0.1:8000/
```

## Test Credentials

```
Admin:
  Username: test_admin
  Password: TestPass123!

Vendor:
  Username: test_vendor
  Password: TestPass123!

Reviewer:
  Username: test_reviewer
  Password: TestPass123!
```

## Quick API Tests (Using curl or Postman)

### Get Token (Example - adjust for actual auth endpoint)
```bash
# Note: Adjust based on your auth implementation
POST http://127.0.0.1:8000/api/token/
{
  "username": "test_admin",
  "password": "TestPass123!"
}
```

### Create Vendor (Admin)
```bash
POST http://127.0.0.1:8000/api/vendors/vendors/
Authorization: Bearer <token>
Content-Type: application/json

{"name": "Test Vendor"}

# Expected: 201 with org auto-populated
```

### Create Template (Admin)
```bash
POST http://127.0.0.1:8000/api/templates/templates/
Authorization: Bearer <token>
Content-Type: application/json

{"name": "Test Template"}

# Expected: 201 with org auto-populated
```

### Create Assessment
```bash
POST http://127.0.0.1:8000/api/assessments/assessments/
Authorization: Bearer <token>
Content-Type: application/json

{"vendor": 1, "template": 1}

# Expected: 201, status=assigned
```

### Submit Assessment (Vendor)
```bash
POST http://127.0.0.1:8000/api/assessments/assessments/1/submit/
Authorization: Bearer <vendor_token>

# Expected: 200 (if ASSIGNED) or 409 (if already submitted)
```

### Review Assessment (Reviewer)
```bash
POST http://127.0.0.1:8000/api/assessments/assessments/1/review/
Authorization: Bearer <reviewer_token>

# Expected: 200 (if SUBMITTED) or 409 (if wrong status)
```

### Approve Assessment (Admin)
```bash
POST http://127.0.0.1:8000/api/assessments/assessments/1/approve/
Authorization: Bearer <admin_token>

# Expected: 200 (if REVIEWED) or 409 (if wrong status)
```

### Test Permission Denied
```bash
# Try to create vendor as vendor
POST http://127.0.0.1:8000/api/vendors/vendors/
Authorization: Bearer <vendor_token>

# Expected: 403 Forbidden
```

### Test Invalid State Transition
```bash
# Try to submit already-submitted assessment
POST http://127.0.0.1:8000/api/assessments/assessments/1/submit/
Authorization: Bearer <vendor_token>

# Expected: 409 Conflict
```

## Database Commands

```powershell
# View database
python manage.py shell
>>> from assessments.models import Assessment
>>> Assessment.objects.all()

# Clear and reseed
rm db.sqlite3
python seed_p0_ready.py

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Files You Need to Know

| File | Purpose |
|------|---------|
| `seed_p0_ready.py` | Setup & seed script |
| `P0_READY_QA_SETUP.md` | Full setup guide |
| `P0_READY_VALIDATION_REPORT.md` | Detailed test cases |
| `config/exceptions.py` | JSON error handler |
| `config/settings.py` | Django configuration |
| `permissions/rbac.py` | Permission classes |
| `db.sqlite3` | Database file |

## Key Configuration

**Exception Handler:** `config.exceptions.custom_exception_handler`
- Returns JSON for all errors
- No HTML debug pages

**Permission Classes Applied to:**
- Templates (ADMIN only)
- Assessments (vendor/reviewer/admin actions)
- Reviews (reviewer/admin only)

**Audit Logging:**
- All critical write actions logged
- Access: GET /api/audit/audit-logs/

## Rollback Commands

```powershell
# If issues, reset to previous state
git revert p0-ready

# Or reset database
rm db.sqlite3
git checkout db.sqlite3
```

## Checking Logs

```powershell
# Django error log (if configured)
tail -f error.log

# Database audit logs
python manage.py shell
>>> from audit.models import AuditLog
>>> AuditLog.objects.all().order_by('-created_at')[:10]

# Git history
git log --oneline -10
```

## Key Fixes Summary

1. **Vendor Create 500** → Fixed by making org read-only + auto-attach
2. **HTML Error Pages** → Fixed by custom exception handler
3. **Permission Checks** → Fixed by dedicated permission classes
4. **State Transitions** → Already enforced with 409 responses
5. **Audit Logging** → Added to all critical endpoints

## Next Steps After Validation

```powershell
# If all tests pass
git push origin main
git push origin p0-ready

# Tag commit info
git show p0-ready

# View all tags
git tag -l
```

## Support

**Issues?**
1. Check error logs in terminal
2. Verify database exists: `ls db.sqlite3`
3. Verify venv activated: `which python`
4. Restart server
5. Reset database and reseed

**Questions?**
- See P0_READY_QA_SETUP.md for detailed guide
- See P0_READY_VALIDATION_REPORT.md for test cases
- Check git log for recent changes
