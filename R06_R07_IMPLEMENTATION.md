# R-06 & R-07 Implementation: Assessment State Machine & Immutable Audit Ledger

## Overview

This implementation covers two critical requirements:

- **R-06**: Assessment state machine hardening with strict transitions
- **R-07**: Immutable append-only audit event ledger with forensic capabilities

Both features work together to provide:
- Guaranteed valid state transitions (conflicts return 409)
- Complete audit trail of all state changes
- Resource tracking and filtering
- Forensic reporting capabilities

## R-06: Assessment State Machine Hardening

### State Diagram

```
assigned → submitted → reviewed ↙ → approved (final)
                      ↘ → remediation → reviewed (loop back)
```

### Valid Transitions

```python
VALID_TRANSITIONS = {
    'assigned': ['submitted'],              # Vendor submits
    'submitted': ['reviewed'],              # Reviewer reviews
    'reviewed': ['approved', 'remediation'], # Approved or needs remediation
    'approved': [],                         # FINAL STATE
    'remediation': ['reviewed'],            # After remediation, re-review
}
```

### Implementation Files

#### `assessments/models.py`
- Updated `Assessment` model with:
  - `STATUS_REMEDIATION` constant
  - Updated `VALID_TRANSITIONS` dictionary
  - Methods: `is_valid_transition()`, `can_transition_to()`

#### `assessments/services.py` (NEW)
- `StateTransitionError`: Exception for invalid transitions
- `AssessmentStateTransitionService`: Service layer providing:
  - `can_transition()`: Validates transition without side effects
  - `transition()`: Executes transition with audit logging
  - `get_valid_next_states()`: Returns available next states

#### `assessments/views.py`
- Updated `AssessmentViewSet` with:
  - `submit()`: assigned → submitted
  - `review()`: submitted → reviewed
  - `approve()`: reviewed → approved
  - `remediate()`: reviewed → remediation (NEW)
  - Proper 409 CONFLICT responses with valid transitions included
  - Returns complete assessment data on success

### API Endpoints

#### Submit Assessment
```
POST /api/assessments/assessments/{id}/submit/
Auth: Vendor role
Response 200: {"message": "...", "status": "submitted", "assessment": {...}}
Response 409: {"error": "Cannot transition from '...' to '...'", "valid_transitions": [...]}
```

#### Review Assessment
```
POST /api/assessments/assessments/{id}/review/
Auth: Reviewer/Admin role
Response 200: Assessment moved to "reviewed" state
Response 409: Invalid transition with available options
```

#### Approve Assessment
```
POST /api/assessments/assessments/{id}/approve/
Auth: Admin role
Response 200: Assessment moved to "approved" with score/risk_level calculated
Response 409: Cannot approve - must be in "reviewed" state first
```

#### Request Remediation
```
POST /api/assessments/assessments/{id}/remediate/
Auth: Reviewer/Admin role
Response 200: Assessment moved to "remediation" state
Response 409: Invalid transition
```

### Error Responses (409 Conflict)

All invalid state transitions return HTTP 409 CONFLICT:

```json
{
  "error": "Cannot transition from 'assigned' to 'approved'. Valid transitions: ['submitted']",
  "current_status": "assigned",
  "valid_transitions": ["submitted"]
}
```

This allows clients to:
1. Detect invalid state attempt
2. Display valid options to user
3. Prevent invalid operations

### Testing

File: `assessments/test_state_machine.py`

Test coverage includes:
- Valid single transitions
- Full transition chains
- Invalid transitions (all permutations)
- Final state enforcement (no transitions from 'approved')
- Remediation loop (remediation → reviewed)
- Audit event creation on each transition
- 409 conflict responses in API

Run tests:
```bash
python manage.py test assessments.test_state_machine
```

## R-07: Immutable Audit Ledger

### Purpose

Every state-changing operation is logged immutably for:
- **Compliance**: Full audit trail for regulatory requirements
- **Forensics**: Investigate what happened, when, and by whom
- **Accountability**: Track all actions to specific users
- **Recovery**: Reconstruct resource state from audit trail

### Implementation Files

#### `audit/models.py` (UPDATED)
- Enhanced `AuditEvent` model with:
  - `user`: FK to actor (user who performed action)
  - `action`: String describing action (e.g., "assessment_transitioned: assigned → submitted")
  - `resource_type`: Type of resource (e.g., "assessment")
  - `resource_id`: ID of affected resource
  - `metadata`: JSONField with:
    - `old_value`, `new_value` (state transitions)
    - `resource` details (vendor_id, template_id, etc.)
    - `actor` details for context
    - Custom application-specific data
  - `created_at`: Auto timestamp (immutable after creation)
  - Indexes on (resource_type, resource_id, created_at) and (user, created_at)

#### `audit/serializers.py` (NEW)
- `AuditEventSerializer`: Read-only, exposes:
  - All event fields
  - `user_details`: Username, email, role (for human-readable reports)

#### `audit/views.py` (UPDATED)
- `AuditEventViewSet`: Read-only API with filtering and search
  - Filters: `resource_type`, `resource_id`, `user`, `action`
  - Search: Full-text on action, username, email
  - Ordering: By `created_at`, `user`, `action`
  - Custom actions for common queries:
    - `/by_resource/`: Complete audit trail for one resource
    - `/by_user/`: All actions by one user
    - `/by_date_range/`: Events in time window
  - Returns 405 METHOD NOT ALLOWED for POST/PUT/DELETE (immutable)

#### `audit/urls.py` (NEW)
- Routes audit endpoints under `/api/audit/`

### API Endpoints

#### List Audit Events
```
GET /api/audit/events/
Query parameters:
  - resource_type: Filter by resource type (e.g., "assessment")
  - resource_id: Filter by resource ID
  - user: Filter by user ID (actor)
  - action: Filter by action type
  - search: Full-text search on action, username, email
  - ordering: Sort field (prefix with - for desc)

Response:
{
  "count": 42,
  "results": [
    {
      "id": 1,
      "user": 5,
      "user_details": {
        "id": 5,
        "username": "reviewer1",
        "email": "reviewer@example.com",
        "role": "reviewer"
      },
      "action": "assessment_transitioned: submitted → reviewed",
      "resource_type": "assessment",
      "resource_id": 123,
      "metadata": {
        "resource": "assessment",
        "resource_id": 123,
        "action": "state_transition",
        "old_value": "submitted",
        "new_value": "reviewed",
        ...
      },
      "created_at": "2026-03-12T10:30:45.123456Z"
    },
    ...
  ]
}
```

#### Get Resource Audit Trail
```
GET /api/audit/events/by_resource/?resource_type=assessment&resource_id=123
Auth: Any authenticated user (org-scoped via tenant guard)

Response:
{
  "resource_type": "assessment",
  "resource_id": 123,
  "event_count": 5,
  "audit_trail": [
    {event 1},
    {event 2},
    {event 3},
    {event 4},
    {event 5}
  ]
}
```

Shows complete lifecycle:
1. Created
2. Vendor submitted
3. Reviewer reviewed
4. Reviewer requested remediation
5. Vendor resubmitted and approved

#### Get User Actions
```
GET /api/audit/events/by_user/?user_id=5
Auth: Any authenticated user

Response:
{
  "user_id": 5,
  "action_count": 23,
  "actions": [
    {action 1 - most recent},
    {action 2},
    ...
  ]
}
```

Useful for admin viewing specific user's activities.

#### Get Events in Date Range
```
GET /api/audit/events/by_date_range/?start_date=2026-01-01T00:00:00Z&end_date=2026-12-31T23:59:59Z
Auth: Any authenticated user (org-scoped)

Response:
{
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-12-31T23:59:59Z",
  "event_count": 156,
  "events": [...]
}
```

Great for:
- Monthly compliance reports
- Investigating incidents in time window
- Performance analysis

### Immutability Enforcement

All write operations return 405 METHOD NOT ALLOWED:

```
POST /api/audit/events/ → 405
PUT /api/audit/events/1/ → 405
PATCH /api/audit/events/1/ → 405
DELETE /api/audit/events/1/ → 405

Response:
{
  "error": "Audit events are immutable - cannot be created, updated, or deleted via API"
}
```

**Database Level**: No triggers or procedures can modify audit events. Append-only by design.

### Integration with State Transitions

When `AssessmentStateTransitionService.transition()` is called:

1. Validates the transition 
2. Updates assessment status
3. **Immediately** creates AuditEvent with:
   - `user`: The user making the transition
   - `action`: "assessment_transitioned: {old} → {new}"
   - `resource_type`: "assessment"
   - `resource_id`: assessment.id
   - `metadata`: Full context (old/new status, vendor, template, etc.)

```python
AssessmentStateTransitionService.transition(
    assessment=assessment,
    new_status="submitted",
    actor_user=vendor_user,
    metadata={"reason": "initial_submission"}
)
# Automatically creates AuditEvent with all details
```

### Testing

File: `audit/test_audit_api.py`

Test coverage includes:
- List/filter/search functionality
- by_resource endpoint (complete lifecycle)
- by_user endpoint (all user actions)
- by_date_range endpoint (time windows)
- Immutability enforcement (no create/update/delete)
- Metadata structure validation
- User details in responses
- Error handling (invalid params, formats)

Run tests:
```bash
python manage.py test audit.test_audit_api
```

## Database Migrations

The implementation requires database migrations for the updated AuditEvent model:

```bash
# Generate migrations
python manage.py makemigrations audit --skip-checks

# Apply migrations
python manage.py migrate audit
```

Fields added to `audit_auditevent`:
- `resource_type` (CharField, nullable)
- `resource_id` (IntegerField, nullable)
- `metadata` (JSONField, default={})
- Indexes for performance

## Use Cases

### 1. Compliance Reporting
```
GET /api/audit/events/?resource_type=assessment&ordering=-created_at
```
Export all assessment changes for auditor review.

### 2. Forensic Investigation
```
GET /api/audit/events/by_resource/?resource_type=assessment&resource_id=789
```
Reconstruct exact timeline of why assessment was approved/rejected.

### 3. User Accountability
```
GET /api/audit/events/by_user/?user_id=42
```
Track all actions by specific reviewer for performance review.

### 4. Incident Response
```
GET /api/audit/events/by_date_range/?start_date=2026-03-10T00:00:00Z&end_date=2026-03-12T23:59:59Z
```
Investigate what changed during incident window.

### 5. State Recovery
```
GET /api/audit/events/by_resource/?resource_type=assessment&resource_id=456
# Parse metadata old_value → new_value to reconstruct state at each timestamp
```
Recover assessment state at any point in time.

## Security Considerations

### Immutability
- Audit events cannot be modified or deleted after creation
- Database constraints ensure append-only
- No audit trail can be tampered with

### Access Control
- All audit APIs require authentication
- Tenant guard ensures users only see their org's events
- Future: Role-based access (e.g., only admins see audit logs)

### Data Retention
- Logs stored indefinitely for compliance
- Future: Archive old logs to cold storage after retention period

## Performance

### Indexes
- `(resource_type, resource_id, created_at)`: Fast resource trail queries
- `(user, created_at)`: Fast user action queries
- `created_at`: Default ordering index

### Pagination
- API defaults to 20 results per page
- Supports limit/offset for large result sets
- Avoid loading millions of events at once

## Future Enhancements

1. **Role-based audit access**: Only admins see audit logs for security events
2. **Audit log retention policies**: Auto-archive after 7 years
3. **Event signing**: Cryptographic signatures to prove logs weren't modified
4. **Webhook notifications**: Real-time audit event notifications
5. **Audit dashboard**: Visual timeline of assessment changes
6. **Advanced search**: Lucene/Elasticsearch index for large audit logs
7. **Bulk export**: Download audit trails as CSV/JSON for external tools

## Summary

**R-06** ensures assessments can only transition through valid states, providing:
- Guaranteed workflow integrity
- Explicit conflict responses (409)
- Clear valid-next-states feedback

**R-07** provides complete forensic audit trail:
- Every state change is logged
- Immutable append-only design
- Resource-centric and user-centric queries
- Full compliance capability

Together, they create a **trustworthy, auditable state machine** for critical assessment workflows.
