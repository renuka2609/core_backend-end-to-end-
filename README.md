# Core Backend API – P0 Validation README

## Setup
```bash
git clone <repo-url>
cd <repo-name>
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver
Swagger:
http://127.0.0.1:8000/swagger/

Authentication
POST /api/auth/login/

{
  "username": "admin",
  "password": "admin123"
}
Authorize using access token.

P0 Swagger Validation Steps
1. Vendor Create (Admin)
POST /api/vendors/

{ "name": "Test Vendor" }
Expected: 201, id auto-generated, org from token, no 500.

2. Template Create (Admin)
POST /api/templates/

{
  "name": "Security Template",
  "description": "P0 validation"
}
Expected: Admin → 201, Vendor → 403.

3. Assessment Create
POST /api/assessments/

{
  "vendor": 1,
  "template": 1
}
Expected: 201, status = assigned.

4. Assessment Submit (Vendor only)
POST /api/assessments/{id}/submit/
Expected:

Vendor → 200

Admin → 403

Duplicate submit → 409

5. Review & Approve
POST /api/assessments/{id}/review/
POST /api/assessments/{id}/approve/
Expected:

Correct order → 200

Wrong order → 409

6. Audit Logs
GET /api/activity/
Logs created for vendor, template, assessment, submit, review, approve.
