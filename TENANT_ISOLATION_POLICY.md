# Tenant Isolation and Multi-Tenant Enforcement Policy

## Overview

This document outlines the tenant isolation policies and enforcement mechanisms implemented across the system to ensure that users can only access data belonging to their organization (tenant).

## Policy Objectives

1. **Data Isolation**: Ensure that data from one tenant is completely isolated from other tenants
2. **Access Control**: Prevent unauthorized cross-tenant access through both list and detail endpoints
3. **Consistency**: Apply uniform tenant filtering across all API endpoints
4. **Security**: Prevent data leakage through query manipulation or direct object access

## Organizational Structure

- **Organization (Tenant)**: The top-level entity representing a customer organization
- **User**: Belongs to exactly one organization
- **Resources**: All resources (assessments, reviews, evidence, etc.) belong to exactly one organization

## Tenant Filtering Implementation

### Core Components

#### 1. TenantAwareQueryGuardMixin

A reusable mixin for ViewSets that enforces tenant filtering on all operations:

**File**: `permissions/tenant_guard.py`

**Key Methods**:
- `get_tenant_value()`: Extracts the user's tenant from user.org, org_id, or tenant_id
- `get_queryset()`: Automatically filters all queries by tenant
- `get_object()`: Verifies object belongs to tenant before returning (prevents direct access)
- `_verify_object_belongs_to_tenant()`: Validates tenant membership

**Configuration per ViewSet**:
- `tenant_filter_field`: The model field to filter by (e.g., 'org', 'org_id')
- `tenant_lookup_path`: For nested relationships (e.g., 'assessment__org')

### Protected Endpoints

The following endpoints are protected with tenant-aware filtering:

#### Assessment Endpoints
- `GET /api/assessments/` - Lists only user's org assessments
- `GET /api/assessments/{id}/` - Denies access to other orgs' assessments
- `POST /api/assessments/` - Creates assessment for user's org
- `PATCH /api/assessments/{id}/` - Denies updates to other orgs' assessments
- `DELETE /api/assessments/{id}/` - Denies deletion of other orgs' assessments

#### Review Endpoints
- `GET /api/reviews/` - Lists only user's org reviews
- `GET /api/reviews/{id}/` - Denies access to other orgs' reviews
- `POST /api/reviews/` - Creates review for user's org
- `PATCH /api/reviews/{id}/` - Denies updates to other orgs' reviews
- `DELETE /api/reviews/{id}/` - Denies deletion of other orgs' reviews

#### Evidence Endpoints
- `GET /api/evidence/` - Lists only evidence from user's org assessments
- `GET /api/evidence/{id}/` - Denies access to other orgs' evidence
- `POST /api/evidence/` - Creates evidence for user's org assessments
- `PATCH /api/evidence/{id}/` - Denies updates to other orgs' evidence
- `DELETE /api/evidence/{id}/` - Denies deletion of other orgs' evidence

#### Response Endpoints
- `GET /api/responses/` - Lists only responses from user's org assessments
- `GET /api/responses/{id}/` - Denies access to other orgs' responses
- `POST /api/responses/` - Creates response for user's org assessments
- `PATCH /api/responses/{id}/` - Denies updates to other orgs' responses
- `DELETE /api/responses/{id}/` - Denies deletion of other orgs' responses

#### Template Endpoints
- `GET /api/templates/` - Lists only user's org templates
- `GET /api/templates/{id}/` - Denies access to other orgs' templates
- `POST /api/templates/` - Creates template for user's org
- `PATCH /api/templates/{id}/` - Denies updates to other orgs' templates
- `DELETE /api/templates/{id}/` - Denies deletion of other orgs' templates

#### Vendor Endpoints
- `GET /api/vendors/` - Lists only user's org vendors
- `GET /api/vendors/{id}/` - Denies access to other orgs' vendors
- `POST /api/vendors/` - Creates vendor for user's org
- `PATCH /api/vendors/{id}/` - Denies updates to other orgs' vendors
- `DELETE /api/vendors/{id}/` - Denies deletion of other orgs' vendors

#### Remediation Endpoints
- `GET /api/remediations/` - Lists only user's org remediations
- `GET /api/remediations/{id}/` - Denies access to other orgs' remediations
- `POST /api/remediations/` - Creates remediation for user's org
- `PATCH /api/remediations/{id}/` - Denies updates to other orgs' remediations
- `DELETE /api/remediations/{id}/` - Denies deletion of other orgs' remediations

#### Dashboard Endpoints
- `GET /api/dashboard/stats/` - Returns stats filtered by user's org
- `GET /api/dashboard/activity-feed/` - Returns activity log filtered by user's org

## Implementation Details

### Model Field Mapping

Different models use different field names for tenant relationship:

| Model | Tenant Field | Type |
|-------|---|---|
| Assessment | org | ForeignKey(Organization) |
| Review | org | ForeignKey(Organization) |
| Template | org | ForeignKey(Organization) |
| Vendor | org | ForeignKey(Organization) |
| Evidence | assessment__org | Nested via Assessment |
| Response | assessment__org | Nested via Assessment |
| Remediation | org_id | IntegerField |

### Query Guard Behavior

#### List Endpoints
```python
# Example: AssessmentViewSet with TenantAwareQueryGuardMixin
# Configuration:
tenant_filter_field = 'org'

# Results in SQL:
SELECT * FROM assessments WHERE org_id = {user.org_id}
```

#### Detail Endpoints
```python
# First retrieves object: obj = super().get_object()
# Then verifies: obj.org == user.org
# If verification fails: raises PermissionDenied (403)
```

#### Nested Relationships
```python
# Example: EvidenceViewSet with nested assessment relationship
# Configuration:
tenant_lookup_path = 'assessment__org'

# Results in SQL:
SELECT * FROM evidence WHERE assessment.org_id = {user.org_id}

# On detail access:
# Verifies: evidence.assessment.org == user.org
```

## Error Responses

### 403 Forbidden - Cross-Tenant Access Attempt
```json
{
  "detail": "You do not have permission to access this resource. It belongs to a different organization."
}
```

### 400 Bad Request - Missing Tenant
```json
{
  "error": "User has no associated tenant/organization"
}
```

### 401 Unauthorized - Unauthenticated
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Testing

Comprehensive integration tests are provided in `test_cross_tenant_access_denial.py`:

**Test Coverage**:
- List endpoint isolation - verifies only own org data is returned
- Detail endpoint denial - verifies foreign org objects cannot be accessed
- Update operation denial - verifies foreign org objects cannot be modified
- Delete operation denial - verifies foreign org objects cannot be deleted
- Unauthenticated access denial - verifies anonymous users are denied

**Running Tests**:
```bash
python manage.py test test_cross_tenant_access_denial.py
# or
python test_cross_tenant_access_denial.py
```

## Adding New Protected Endpoints

To add tenant isolation to a new ViewSet:

### Step 1: Import the Mixin
```python
from permissions.tenant_guard import TenantAwareQueryGuardMixin
```

### Step 2: Add to ViewSet
```python
class MyResourceViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = MyResource.objects.all()
    serializer_class = MyResourceSerializer
    permission_classes = [IsAuthenticated]
    
    # Set the tenant field for this model
    tenant_filter_field = 'org'  # or 'org_id', or nested path like 'parent__org'
```

### Step 3: Verify in Tests
Add test cases in `test_cross_tenant_access_denial.py` to verify:
- List isolation
- Detail access denial
- Create operation
- Update denial
- Delete denial

## Security Considerations

### What This Protects Against
- ✅ Unauthorized list queries showing foreign data (SQL injection via Django ORM)
- ✅ Direct URL access to foreign objects (e.g., `/api/assessments/999/`)
- ✅ Bulk operations on foreign objects
- ✅ Cross-tenant data leakage via API responses

### What This Doesn't Protect Against
- ❌ Application-level bugs in serializers (validate custom logic)
- ❌ Direct database access (limit database account permissions)
- ❌ Middleware vulnerabilities (keep middleware updated)
- ❌ Logging/audit data exposure (implement audit log filtering)

## Maintenance

### Audit Checklist
- [ ] All ViewSets inherit from TenantAwareQueryGuardMixin
- [ ] Each ViewSet sets correct tenant_filter_field
- [ ] No direct QuerySet creation (always use get_queryset())
- [ ] perform_create() assigns correct org/tenant to new objects
- [ ] Nested relationships use tenant_lookup_path
- [ ] Dashboard/aggregation endpoints filter by tenant

### Validation Commands
```bash
# Check all ViewSets have mixin
grep -r "TenantAwareQueryGuardMixin" . --include="*.py"

# Check for get_queryset overrides (should use mixin)
grep -r "def get_queryset" . --include="*.py" | grep -v tenant_guard

# Run full test suite
python test_cross_tenant_access_denial.py
```

## Related Files

- **Mixin Implementation**: `permissions/tenant_guard.py`
- **Integration Tests**: `test_cross_tenant_access_denial.py`
- **Middleware Context**: `middleware/tenant_middleware.py`, `orgs/middleware.py`
- **RBAC Configuration**: `permissions/rbac.py`

## Compliance

This implementation ensures compliance with:
- Multi-tenant SaaS security best practices
- Principle of least privilege
- Defense in depth (multiple verification points)
- Secure by default (all ViewSets must opt-in to mixin)
