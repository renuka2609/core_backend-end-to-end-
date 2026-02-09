# Core Backend – P0 Ready (Canonical Repo)

## Canonical Backend
This repository is the single canonical backend to be used by QA and the team for P0 validation.

## Setup & Run Steps

1. Create and activate virtual environment
   python -m venv venv
   venv\Scripts\activate

2. Install dependencies
   pip install -r requirements.txt

3. Run migrations
   python manage.py migrate

4. Seed data
   python manage.py seed

Seed creates:
- Organization
- Admin user
- Vendor + vendor user
- Template + version + section + questions
- Sample assessment
- Sample response

---

## Authentication
- Login using POST /api/auth/login/
- Use access token in Swagger Authorize
- Org is auto-attached from authenticated user (no manual org in payload)

---

## P0 Demo Flow (Swagger Steps)

1. Vendor Create
   POST /api/vendors/
   Body:
   {
     "name": "Test Vendor",
     "primary_contact_email": "vendor@test.com",
     "industry": "IT",
     "initial_risk_tier": "MEDIUM"
   }

   Expected:
   201 success
   401 no token
   403 wrong role

2. Template Create
   POST /api/templates/
   Verify with GET /api/templates/

3. Assign Assessment
   POST /api/assessments/
   {
     "vendor": 1,
     "template": 1
   }

4. Add Vendor Responses
   POST /api/responses/responses/

5. Submit Assessment
   POST /api/assessments/{id}/submit/
   Expected:
   200 valid submit
   409 invalid transition

6. Reviewer Decision
   POST /api/reviews/{id}/decision/
   {
     "decision": "APPROVE"
   }
   Valid values: APPROVE, REJECT, REMEDIATION_REQUIRED

7. Remediation (if required)
   POST /api/remediations/{id}/respond/
   POST /api/remediations/{id}/close/

---

## Workflow Enforcement (P0)

- 401 → No token
- 403 → Wrong role
- 409 → Invalid workflow transition
- 200 / 201 → Valid action

Inline role checks removed.
Permissions enforced via permission classes.

---

## Audit Logs
Audit logs generated for:
- Vendor create/update
- Template create/version
- Assessment create/submit
- Review decision
- Remediation actions
- Approval / renewal

---

## Proof Attached
- Swagger screenshots for P0 endpoints
- Seed command output
- End-to-end demo flow executed

---

## Status
P0 conformance gaps closed.
Backend is QA-ready and demo-ready.

Owner: Renuka Deshpande
