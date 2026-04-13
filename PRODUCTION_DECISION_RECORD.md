# Production Architecture Decision Record (ADR)

**Date:** April 12, 2026  
**Status:** ACTIVE  
**Decision Maker:** Architecture Team

---

## Executive Summary ✅

This document formalizes the production backend architecture and deprecates duplicate runtime paths.

**Decision:** Single unified Django backend at `/core_backend(end to end)` with VRM duplicate copies deprecated.

---

## Architecture Decision (ADR-001)

### Problem
- Duplicate VRM runtime paths causing RBAC inconsistency
- Legacy permission imports mixed with new central policy
- Tenant isolation not uniformly enforced
- Multiple audit implementations causing maintenance burden

### Decision
**Single Source of Truth:** Deprecate VRM duplicate backends. All production traffic routes through:
- **Path:** `/core_backend(end to end)`
- **Entry Point:** `config.urls` (main)
- **Settings:** `config.settings`
- **Apps:** accounts, assessments, reviews, vendors, templates, evidence, remediations, responses, audit, orgs, users

### Rationale
1. **Maintainability** - Single codebase eliminates sync issues
2. **Security** - Unified permission enforcement via `permissions/rbac_policy.py`
3. **Consistency** - Tenant isolation enforced via `TenantAwareQueryGuardMixin` everywhere
4. **Audit** - Single append-only ledger in `audit/models.py`
5. **Compliance** - Centralized JWT, rate limiting, security headers

### Implementation Status
✅ **ENACTED:**
- Core backend fully functional
- All main views using central RBAC policy
- Tenant guards applied to list/detail endpoints
- JWT token rotation enabled
- Security headers active
- Audit logging working

### Deprecation Plan

#### Phase 1: Migrate VRM References (COMPLETED)
| Path | Status | Action Taken |
|------|--------|--------------|
| `vrm/vendors/views.py` | DEPRECATED | ✅ Updated to use rbac_policy + TenantAwareQueryGuardMixin |
| `vrm/reviews/views.py` | DEPRECATED | ✅ Updated to use rbac_policy + TenantAwareQueryGuardMixin |
| All VRM audit services | DEPRECATED | Uses main audit app only |
| `vrm/seed_data` | DEPRECATED | Use root `seed_p0_ready.py` |

#### Phase 2: URL Consolidation
**Current (Production):**
```
Main: /core_backend(end to end)/config/urls.py
```

**VRM copies (DO NOT USE):**
```
Deprecated: /vrm/config/urls.py (not in active INSTALLED_APPS)
```

**Action:** VRM app remains for backward compatibility but is not loaded. All traffic through main URLs.

#### Phase 3: Shutdown Timeline
- **Now (April 2026):** VRM views updated to align with main RBAC
- **Q2 2026:** Remove VRM imports where no active references
- **Q3 2026:** Archive VRM as historical reference only

---

## Component Architecture

### RBAC Policy (Central Authority)
**Location:** `permissions/rbac_policy.py`  
**Exported via:** `permissions/rbac.py`

| Component | Location | Status |
|-----------|----------|--------|
| Role constants | `permissions/constants.py` | ✅ Active |
| Policy matrix | `rbac_policy.RBAC_POLICY_MATRIX` | ✅ Active |
| Permission classes | `rbac_policy.IsAdmin`, `IsReviewer`, `IsVendor` | ✅ Active |
| Workflow actions | `rbac_policy.WorkflowAction` | ✅ Active |
| Policy enforcement | `rbac_policy.WorkflowActionPermission` | ✅ Active |

**Rule:** All views import from `permissions.rbac_policy`

### Tenant Isolation (Mandatory)
**Location:** `permissions/tenant_guard.py`  
**Class:** `TenantAwareQueryGuardMixin`

| Endpoint | Mixin Applied | Status |
|----------|---|---|
| `/api/assessments/` | ✅ AssessmentViewSet | ✅ Active |
| `/api/reviews/` | ✅ ReviewViewSet | ✅ Active |
| `/api/vendors/` | ✅ VendorViewSet | ✅ Active |
| `/api/templates/` | ✅ TemplateViewSet | ✅ Active |
| `/api/responses/` | ✅ ResponseViewSet | ✅ Active |
| `/api/evidence/` | ✅ EvidenceViewSet | ✅ Active |
| `/api/remediations/` | ✅ RemediationViewSet | ✅ Active |

**Rule:** Every list/detail endpoint must extend `TenantAwareQueryGuardMixin`

### State Machine (Strict Transitions)
**Location:** `assessments/models.py:Assessment`

**Valid Flow:**
```
assigned → submitted → reviewed → {approved, remediating}
  ↓         (vendor)    (reviewer)  (admin/reviewer)
  repeat
  after
  remediation
  
approved → closed → renewed → assigned
(admin)    (system) (periodic) (restart)
```

**Enforcement:** 
- Model: `Assessment.VALID_TRANSITIONS` dict
- Service: `AssessmentStateTransitionService.transition()`
- HTTP Response: 409 CONFLICT for invalid transitions

**Rule:** All workflows must use `AssessmentStateTransitionService`

### Audit Logging (Append-Only)
**Location:** `audit/models.py:AuditEvent`

| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| user | FK(User) | ✅ | Actor |
| org | FK(Org) | ✅ | Tenant context |
| action | CharField | ✅ | Action type |
| resource_type | CharField | ✅ | Assessment/Review/etc |
| resource_id | IntegerField | ✅ | Resource ID |
| metadata | JSONField | - | old/new values, context |
| created_at | DateTime | ✅ | Auto timestamp |

**Immutability:** Read-only API, no update/delete endpoints

**Rule:** All state changes must call `audit.services.log_event()`

### Security Stack
**Middleware Stack (in order):**
1. `django.middleware.security.SecurityMiddleware` - HTTPS redirects
2. `config.security.SecurityHeadersMiddleware` - CSP, HSTS, etc
3. `config.security.RateLimitMiddleware` - Per-user/IP limiting
4. `config.middleware.InputValidationMiddleware` - Input sanitization
5. `config.exceptions.custom_exception_handler` - JSON error responses (not HTML)

**Exception Handler:**
```python
'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler'
```

**JWT:**
- Access token lifetime: 30 minutes
- Refresh token lifetime: 1 day
- Rotation: Enabled (`ROTATE_REFRESH_TOKENS: True`)
- Blacklist: Enabled (`BLACKLIST_AFTER_ROTATION: True`)

---

## Compliance Matrix

### P0.1: RBAC Consistency
| Requirement | Implementation | Status |
|-------------|---|---|
| Centralized role constants | `permissions/constants.py` | ✅ |
| No hardcoded role strings | grep for 'admin'/'reviewer'/'vendor' literals | ✅ Zero |
| All views use central policy | Import from `rbac_policy` | ✅ All active |
| Permission class inheritance | Extend `BasePermission` from `rbac_policy` | ✅ |

**Verification:** `python demonstrate_p0_fixes.py → TEST 1`

### P0.2: 409 Conflict Enforcement
| Requirement | Implementation | Status |
|-------------|---|---|
| State machine defined | `Assessment.VALID_TRANSITIONS` | ✅ |
| Invalid transitions blocked | `can_transition_to()` validation | ✅ |
| 409 HTTP response | `AssessmentStateTransitionService.transition()` | ✅ |
| Error message clarity | Endpoint returns valid transitions | ✅ |

**Verification:** `python demonstrate_p0_fixes.py → TEST 2`

### P0.3: Audit Logging
| Requirement | Implementation | Status |
|-------------|---|---|
| All critical actions logged | Calls to `log_event()` in services | ✅ |
| Immutable records | Read-only API, `get_queryset()` filters org | ✅ |
| Actor context preserved | `user` and `org` ForeignKeys | ✅ |
| Metadata captures old/new | `metadata` JSONField | ✅ |

**Verification:** `python demonstrate_p0_fixes.py → TEST 4`

### P0.4: Org Isolation
| Requirement | Implementation | Status |
|-------------|---|---|
| List filtering by org | `TenantAwareQueryGuardMixin` | ✅ All views |
| Detail access check | `.get_object()` + org validation | ✅ Mixin handles |
| Cross-org denial (403) | `PermissionDenied` raised | ✅ |
| Search/filter sanitization | Query restricted to user's org | ✅ |

**Verification:** `python test_cross_tenant_access_denial.py`

---

## Production Checklist

### Before Deploying
- [ ] All 4 P0 tests passing: `pytest -v`
- [ ] Seed script runs cleanly: `python seed_p0_ready.py`
- [ ] Swagger UI loads at `/api/docs/`
- [ ] Can login with test users (see credentials below)
- [ ] Token refresh works (30-minute access lifetime)
- [ ] Invalid state transitions return 409
- [ ] Cross-org access returns 403
- [ ] Audit logs appear in `/api/audit/events/`

### Test Users
| Role | Username | Password | Tests |
|------|----------|----------|-------|
| Admin | `test_admin` | `TestPass123!` | All operations |
| Reviewer | `test_reviewer` | `TestPass123!` | Review/approve |
| Vendor | `test_vendor` | `TestPass123!` | Submit/create evidence |

### Critical Endpoints to Test
1. **Auth:** `POST /api/accounts/login/`
2. **RBAC:** `GET /api/assessments/` (org isolation)
3. **409 Conflict:** `POST /api/assessments/{id}/approve/` (invalid transition)
4. **Audit:** `GET /api/audit/events/` (view logs)

---

## Monitoring & Alerting

### Key Metrics
1. **Auth failures** - Track in logs/prometheus
2. **409 conflicts** - Expected during tests, monitor for patterns
3. **403 Forbidden** - Should only occur for cross-org or invalid role
4. **Audit event count** - Should grow with usage
5. **JWT refresh rate** - Should be < 10% of requests

### Alerts
- 5+ failed login in 1 minute → Rate limit activ ated
- 403 rate > 5% for same user → Possible escalation attempt
- Audit lag > 5 seconds → DB performance issue
- Memory usage > 500MB → Cache growth

---

## Rollback Plan

If issues occur post-deployment:

1. **Symptom:** 403 errors for valid users
   - **Cause:** Tenant filter too strict
   - **Fix:** Review `TenantAwareQueryGuardMixin.get_queryset()`

2. **Symptom:** Audit logs not appearing
   - **Cause:** Service layer not calling `log_event()`
   - **Fix:** Add `log_event()` calls to business logic

3. **Symptom:** 409 conflicts too frequent
   - **Cause:** Invalid state machine definition
   - **Fix:** Review `Assessment.VALID_TRANSITIONS`

---

## References

- **RBAC Policy:** `permissions/rbac_policy.py`
- **Tenant Guard:** `permissions/tenant_guard.py`
- **State Machine:** `assessments/services.py`
- **Audit API:** `audit/views.py`
- **URL Config:** `config/urls.py`
- **Settings:** `config/settings.py`

---

## Sign-Off

**Architecture Approved:**  April 12, 2026  
**By:** Engineering Team  
**Status:** ACTIVE - Production Ready
