# RBAC Security Assessment - Issues & Action Items

**Date:** April 4, 2026  
**Assessment:** Comprehensive RBAC implementation audit  
**Priority Levels:** P0 (Critical) → P2 (Enhancement)

---

## Executive Summary

### Current State
- ✅ **Centralized RBAC policy matrix** is well-designed and documented
- ✅ **3 main apps** (Assessments, Reviews, Vendors) have comprehensive implementation
- ⚠️ **4 apps** have incomplete implementations missing workflow action checks
- 🔴 **1 app** (Remediations) has critical security gaps

### Risk Profile
- **Critical Issues:** 1
- **High Priority Issues:** 4  
- **Medium Priority Issues:** 2
- **Status:** Ready for remediation

---

## Issues by Severity

## 🔴 CRITICAL (Fix immediately)

### 1. Remediations - No Permission Validation

**File:** `remediations/views.py`  
**Severity:** CRITICAL  
**Risk:** Unauthenticated users can perform remediation actions

**Current Code:**
```python
class RemediationViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Remediation.objects.all()
    serializer_class = RemediationSerializer
    tenant_filter_field = 'org_id'
    # ❌ NO permission_classes defined!

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        # ❌ NO permission check
        obj.response = request.data.get("response", "")

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        # ❌ NO permission check
        obj.status = "closed"
```

**Expected Behavior:**
- `respond()` → VENDOR only
- `close()` → ADMIN, REVIEWER only
- `create()` → ADMIN, REVIEWER only

**Fix Required:**
```python
from rest_framework.permissions import IsAuthenticated
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
)

class RemediationViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Remediation.objects.all()
    serializer_class = RemediationSerializer
    permission_classes = [IsAuthenticated]  # ADD THIS
    tenant_filter_field = 'org_id'

    def perform_create(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.REMEDIATION_CREATE
        )
        obj = serializer.save(org_id=self.request.user.org_id)
        log_event(user=self.request.user, action="remediation_created", obj=obj)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.REMEDIATION_RESPOND
        )
        obj = self.get_object()
        if obj.status != "open":
            return Response({"error": "invalid state"}, status=409)
        obj.vendor_response = request.data.get("response", "")
        obj.status = "responded"
        obj.save()
        log_event(user=request.user, action="remediation_responded", obj=obj)
        return Response({"status": "responded"})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.REMEDIATION_CLOSE
        )
        obj = self.get_object()
        if obj.status != "responded":
            return Response({"error": "invalid state"}, status=409)
        obj.status = "closed"
        obj.save()
        trigger_scoring(obj.assessment.id)
        log_event(user=request.user, action="remediation_closed", obj=obj)
        return Response({"status": "closed"})
```

**Impact if not fixed:** CRITICAL
- Unauthenticated users can access/modify remediations
- Vendors can close remediations (should be admin/reviewer only)
- No tenant isolation enforced

---

## 🔴 HIGH PRIORITY (Fix in next sprint)

### 2. Templates - Missing Workflow Action Checks

**File:** `templates/views.py`  
**Severity:** HIGH  
**Risk:** Any authenticated user can create/edit/delete templates

**Current Code:**
```python
class TemplateViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]  # ❌ Should be IsAdmin
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        serializer.save(org=self.request.user.org)
        # ❌ No permission check
```

**Expected Behavior:**
- Only ADMIN can create/edit/delete templates
- REVIEWER, VENDOR can view templates

**Fix Required:**
```python
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
)

class TemplateViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]  # Keep for view access
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.TEMPLATE_CREATE
        )
        serializer.save(org=self.request.user.org)
    
    def perform_update(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.TEMPLATE_EDIT
        )
        return super().perform_update(serializer)
    
    def perform_destroy(self, instance):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.TEMPLATE_DELETE
        )
        return super().perform_destroy(instance)
```

**Impact if not fixed:** HIGH
- Vendors could create templates (should be admin only)
- Template consistency not guaranteed
- Audit trail incomplete

---

### 3. Responses - Missing Workflow Action Checks

**File:** `responses/views.py`  
**Severity:** HIGH  
**Risk:** Any authenticated user can create/submit responses

**Current Code:**
```python
class ResponseViewSet(TenantAwareQueryGuardMixin, ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]  # ❌ No role check
    tenant_filter_field = 'assessment__org'
    tenant_lookup_path = 'assessment__org'

    def perform_create(self, serializer):
        response = serializer.save()
        # ❌ No permission check

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        obj = self.get_object()
        # ❌ No permission check - any user can submit!
        obj.submitted = True
        obj.save()
```

**Expected Behavior:**
- CREATE: ADMIN, VENDOR
- SUBMIT: VENDOR only
- VIEW/EDIT: ADMIN, REVIEWER, VENDOR

**Fix Required:**
```python
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
)

class ResponseViewSet(TenantAwareQueryGuardMixin, ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_field = 'assessment__org'
    tenant_lookup_path = 'assessment__org'

    def perform_create(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.RESPONSE_CREATE
        )
        response = serializer.save()
        log_event(user=self.request.user, action="response_created", ...)

    def perform_update(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.RESPONSE_EDIT
        )
        response = serializer.save()
        log_event(user=self.request.user, action="response_updated", ...)

    def perform_destroy(self, instance):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.RESPONSE_DELETE
        )
        eid = instance.id
        assessment_id = instance.assessment.id
        instance.delete()
        log_event(user=self.request.user, action="response_deleted", ...)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.RESPONSE_SUBMIT
        )
        obj = self.get_object()
        if getattr(obj, "submitted", False):
            return DRFResponse({"error": "Already submitted"}, status=409)
        obj.submitted = True
        obj.save()
        log_event(user=request.user, action="response_submitted", ...)
        return DRFResponse({"status": "submitted"})
```

**Impact if not fixed:** HIGH
- Reviewers could submit responses (should be vendor only)
- Response integrity not guaranteed
- Audit trail incomplete

---

### 4. Evidence - Missing Workflow Action Checks

**File:** `evidence/views.py`  
**Severity:** HIGH  
**Risk:** Any authenticated user can create/edit/delete evidence

**Current Code:**
```python
class EvidenceViewSet(TenantAwareQueryGuardMixin, ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]  # ❌ No role check
    tenant_filter_field = 'assessment__org'
    tenant_lookup_path = 'assessment__org'

    def perform_create(self, serializer):
        evidence = serializer.save(uploaded_by=self.request.user)
        # ❌ No permission check

    def perform_destroy(self, instance):
        # ❌ No permission check
        eid = instance.id
        assessment_id = instance.assessment.id
        instance.delete()
```

**Expected Behavior:**
- CREATE/EDIT: ADMIN, VENDOR
- DELETE: ADMIN, VENDOR
- VIEW: ADMIN, REVIEWER, VENDOR

**Fix Required:**
```python
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
)

class EvidenceViewSet(TenantAwareQueryGuardMixin, ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_field = 'assessment__org'
    tenant_lookup_path = 'assessment__org'

    def perform_create(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.EVIDENCE_CREATE
        )
        evidence = serializer.save(uploaded_by=self.request.user)
        log_event(user=self.request.user, action="evidence_created", ...)

    def perform_update(self, serializer):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.EVIDENCE_EDIT
        )
        evidence = serializer.save()
        log_event(user=self.request.user, action="evidence_updated", ...)

    def perform_destroy(self, instance):
        # ADD THIS
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.EVIDENCE_DELETE
        )
        eid = instance.id
        assessment_id = instance.assessment.id
        instance.delete()
        log_event(user=self.request.user, action="evidence_deleted", ...)
```

**Impact if not fixed:** HIGH
- Reviewers could delete evidence (should be admin/vendor only)
- Audit compliance compromised
- Evidence tampering possible

---

## 🟠 MEDIUM PRIORITY (Fix in next quarter)

### 5. Dashboard - No Role-Based Stats Filtering

**File:** `dashboard/views.py`  
**Severity:** MEDIUM  
**Risk:** Incorrect users might see admin-only statistics

**Current Code:**
```python
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ❌ DASHBOARD_STATS should be admin/reviewer only
        # but no check enforces this
        user = request.user
        user_org = getattr(user, 'org', None)
        
        stats = {
            "total_assessments": Assessment.objects.filter(org=user_org).count(),
            "total_reviews": Review.objects.filter(org=user_org).count(),
            # ...
        }
        # Vendor can see this but DASHBOARD_STATS action is admin/reviewer only
```

**Expected Behavior:**
- DASHBOARD_VIEW: Available to ADMIN, REVIEWER, VENDOR
- DASHBOARD_STATS: Available to ADMIN, REVIEWER only (currently missing check)

**Fix Required:**
```python
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
    RBACPolicyHelper,
    RoleType,
)

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ADD THIS - enforce DASHBOARD_STATS role check
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.DASHBOARD_STATS
        )
        
        user = request.user
        user_org = getattr(user, 'org', None)
        if not user_org:
            return Response({"error": "User has no organization"}, status=400)
        
        stats = {
            "total_assessments": Assessment.objects.filter(org=user_org).count(),
            "total_reviews": Review.objects.filter(org=user_org).count(),
            "total_remediations": Remediation.objects.filter(org_id=user_org.id).count(),
        }
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

class DashboardActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ADD THIS - enforce DASHBOARD_VIEW role check
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.DASHBOARD_VIEW
        )
        
        user = request.user
        user_org = getattr(user, 'org', None)
        if not user_org:
            return Response({"error": "User has no organization"}, status=400)
        
        logs = AuditLog.objects.filter(org=user_org).order_by('-timestamp')[:50]
        feed = [
            {
                "actor": log.user.username if log.user else "System",
                "action": log.action,
                "entity": log.entity if hasattr(log, 'entity') else "Unknown",
                "timestamp": log.timestamp if hasattr(log, 'timestamp') else None,
            }
            for log in logs
        ]
        serializer = ActivityFeedSerializer(feed, many=True)
        return Response(serializer.data)
```

**Impact if not fixed:** MEDIUM
- Vendors see admin stats they shouldn't
- Compliance audits might flag this
- User confusion about what they can access

---

### 6. Audit - No Tenant Isolation

**File:** `audit/views.py`  
**Severity:** MEDIUM  
**Risk:** Users see audit logs from other organizations

**Current Code:**
```python
class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all().order_by('-created_at')  # ❌ No org filter!
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]
    # ❌ No TenantAwareQueryGuardMixin
```

**Expected Behavior:**
- Regular users see only their org's audit logs
- Admins might be able to see all orgs' logs (optional based on business rules)

**Fix Required:**
```python
from permissions.tenant_guard import TenantAwareQueryGuardMixin

class AuditEventViewSet(TenantAwareQueryGuardMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all().order_by('-created_at')
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_field = 'org'  # Assuming AuditEvent has org field
    # Or if nested: tenant_lookup_path = 'user__org'
```

**Impact if not fixed:** MEDIUM
- Cross-tenant data leakage
- Compliance violation (audit logs must be segregated)
- User privacy concern

---

## 📋 Summary of Changes Needed

### By File

| File | Changes | Priority |
|------|---------|----------|
| `remediations/views.py` | Add `permission_classes`, `perform_create`, workflow checks in `respond()` and `close()` | **P0** |
| `responses/views.py` | Add workflow checks in `perform_create`, `perform_update`, `perform_destroy`, `submit()` | **P1** |
| `evidence/views.py` | Add workflow checks in `perform_create`, `perform_update`, `perform_destroy` | **P1** |
| `templates/views.py` | Add workflow checks in `perform_create`, `perform_update`, `perform_destroy` | **P1** |
| `dashboard/views.py` | Add workflow action checks in both views | **P2** |
| `audit/views.py` | Add `TenantAwareQueryGuardMixin` and tenant filtering | **P2** |

### Implementation Effort
- **P0 (Critical):** 2-3 hours (Remediations)
- **P1 (High):** 4-5 hours (Templates, Responses, Evidence)
- **P2 (Medium):** 2-3 hours (Dashboard, Audit)

**Total Estimated Effort:** 8-11 hours

---

## Testing Checklist After Fixes

- [ ] Vendor cannot create templates (should get 403)
- [ ] Vendor cannot submit responses created by admin (should get 403)
- [ ] Reviewer cannot close remediations (should get 403)
- [ ] Vendor cannot access audit logs from other org (should get 403)
- [ ] Vendor cannot see admin-only dashboard stats (should get 403)
- [ ] Admin can perform all actions (should get 200)
- [ ] Reviewer can review assessments (should get 200)
- [ ] Unauthenticated users get 401 on all endpoints

---

## References
- [RBAC_IMPLEMENTATION_SUMMARY.md](RBAC_IMPLEMENTATION_SUMMARY.md) - Full implementation details
- [RBAC_QUICK_REFERENCE.md](RBAC_QUICK_REFERENCE.md) - Quick lookup guide
- `permissions/rbac_policy.py` - Central permission definitions
- `permissions/constants.py` - Role constants

---

**Status:** Ready for sprint planning  
**Last Updated:** April 4, 2026
