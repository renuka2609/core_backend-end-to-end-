#!/usr/bin/env python
"""
P0-Ready Setup & Seed Script for QA

This script sets up the database with test data for full workflow validation.
Run this to reproduce the P0-ready state.

STEPS FOR QA:
1. Activate Python environment: .venv/Scripts/activate.ps1
2. Run: python seed_p0_ready.py
3. Start server: python manage.py runserver
4. Validate endpoints using the test list at the end of this file
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from users.models import User
from orgs.models import Organization
from vendors.models import Vendor
from templates.models import Template, TemplateVersion, TemplateSection, TemplateQuestion
from assessments.models import Assessment
from audit.models import AuditLog
from permissions.constants import Roles

User_model = get_user_model()

print("=" * 80)
print("P0-READY SETUP & SEED SCRIPT")
print("=" * 80)

# Step 1: Run migrations
print("\n[STEP 1] Running migrations...")
try:
    call_command('migrate', verbosity=1)
    print("✅ Migrations completed")
except Exception as e:
    print(f"❌ Migration error: {e}")
    sys.exit(1)

# Step 2: Clear old data (optional - comment out if you want to keep existing data)
print("\n[STEP 2] Clearing old test data...")
try:
    User_model.objects.filter(username__startswith='test_').delete()
    Organization.objects.filter(name__startswith='Test Org').delete()
    print("✅ Old data cleared")
except Exception as e:
    print(f"⚠️  Warning clearing old data: {e}")

# Step 3: Create organizations
print("\n[STEP 3] Creating test organizations...")
org1, _ = Organization.objects.get_or_create(
    name="Test Organization 1",
)
print(f"✅ Created org: {org1.name}")

# Step 4: Create users with different roles
print("\n[STEP 4] Creating test users...")

users_data = [
    {"username": "test_admin", "email": "admin@test.com", "password": "TestPass123!", "role": Roles.ADMIN},
    {"username": "test_vendor", "email": "vendor@test.com", "password": "TestPass123!", "role": Roles.VENDOR},
    {"username": "test_reviewer", "email": "reviewer@test.com", "password": "TestPass123!", "role": Roles.REVIEWER},
]

users = {}
for user_data in users_data:
    user, created = User_model.objects.get_or_create(
        username=user_data["username"],
        defaults={
            "email": user_data["email"],
            "role": user_data["role"],
            "org": org1,
            "is_staff": user_data["role"] == Roles.ADMIN,
        }
    )
    if created:
        user.set_password(user_data["password"])
        user.save()
        print(f"✅ Created user: {user.username} ({user.role})")
    else:
        print(f"⚠️  User already exists: {user.username}")
    users[user_data["username"]] = user

# Step 5: Create vendors
print("\n[STEP 5] Creating test vendors...")

vendors = []
vendor_names = ["Acme Corp", "Tech Solutions Inc", "Global Services Ltd"]

for vname in vendor_names:
    vendor, created = Vendor.objects.get_or_create(
        name=vname,
        org=org1,
    )
    if created:
        print(f"✅ Created vendor: {vendor.name}")
    else:
        print(f"⚠️  Vendor already exists: {vendor.name}")
    vendors.append(vendor)

# Step 6: Create templates
print("\n[STEP 6] Creating templates with versions...")

template, t_created = Template.objects.get_or_create(
    name="Compliance Assessment Template",
    org=org1,
    defaults={"description": "Standard compliance template"}
)
print(f"✅ Created template: {template.name}" if t_created else f"⚠️  Template exists: {template.name}")

# Create template version
version, v_created = TemplateVersion.objects.get_or_create(
    template=template,
    version=1,
)
print(f"✅ Created template version: v{version.version}" if v_created else f"⚠️  Version exists: v{version.version}")

# Add template sections and questions
section, s_created = TemplateSection.objects.get_or_create(
    template_version=version,
    title="Security Controls",
    defaults={"description": "Assessment of security controls"}
)
print(f"✅ Created section: {section.title}" if s_created else f"⚠️  Section exists: {section.title}")

question_texts = [
    "Do you have multi-factor authentication enabled?",
    "Are all systems patched and updated?",
    "Do you have a documented incident response plan?",
]

for qtext in question_texts:
    question, q_created = TemplateQuestion.objects.get_or_create(
        section=section,
        text=qtext,
        defaults={"question_type": "yes/no"}
    )
    if q_created:
        print(f"  ✅ Added question: {qtext[:50]}...")

# Step 7: Create assessments
print("\n[STEP 7] Creating assessments...")

for i, vendor in enumerate(vendors[:2]):  # Create assessments for first 2 vendors
    assessment, a_created = Assessment.objects.get_or_create(
        org=org1,
        vendor=vendor,
        template=template,
        defaults={"status": Assessment.STATUS_ASSIGNED}
    )
    if a_created:
        print(f"✅ Created assessment: {vendor.name} - {template.name}")
    else:
        print(f"⚠️  Assessment already exists: {vendor.name}")

# Step 8: Verify database state
print("\n[STEP 8] Verifying database state...")
print(f"  • Organizations: {Organization.objects.count()}")
print(f"  • Users: {User_model.objects.count()}")
print(f"  • Vendors: {Vendor.objects.count()}")
print(f"  • Templates: {Template.objects.count()}")
print(f"  • Assessments: {Assessment.objects.count()}")

print("\n" + "=" * 80)
print("✅ SETUP COMPLETE - Database ready for P0 validation")
print("=" * 80)

print("\n📋 ENVIRONMENT CONFIGURATION:")
print("  • DATABASE: SQLite (db.sqlite3)")
print("  • DEBUG: True")
print("  • ALLOWED_HOSTS: ['*', 'testserver']")
print("  • EXCEPTION_HANDLER: Custom JSON handler (config.exceptions.custom_exception_handler)")

print("\n🧪 TEST CREDENTIALS:")
for username, user in users.items():
    print(f"  • {username}: {user.get_role_display()}")
    print(f"      Email: {user.email}")
    print(f"      Password: TestPass123!")

print("\n📝 QA VALIDATION STEPS:")
print("  1. Start server: python manage.py runserver")
print("  2. Test each endpoint below with the appropriate user credentials")
print("  3. Verify: 400/403 for permission errors, 409 for invalid transitions, 500 NEVER")

print("\n✅ TEST ENDPOINT LIST:")
print("""
VENDORS:
  POST /api/vendors/vendors/
    Payload: {"name": "New Vendor Corp"}
    Expected: 201 (org auto-attached from token)
    Auth: admin/reviewer only
  
TEMPLATES:
  POST /api/templates/templates/
    Payload: {"name": "New Template", "description": "Test"}
    Expected: 201 (org auto-attached)
    Auth: admin only
  
  POST /api/templates/template-versions/
    Payload: {"template": 1, "version": 2}
    Expected: 201 (admin only)
    Auth: admin only

ASSESSMENTS:
  POST /api/assessments/assessments/
    Payload: {"vendor": 1, "template": 1}
    Expected: 201 (org auto-attached, status=assigned)
  
  POST /api/assessments/assessments/{id}/submit/
    Expected: 200 or 409 (if invalid transition)
    Auth: vendor only
    • 409: "Cannot transition from 'assigned' to 'submitted'" (if status wrong)
    • 200: Success
  
  POST /api/assessments/assessments/{id}/review/
    Expected: 200 or 409
    Auth: reviewer/admin only
    • 409: Invalid transition
    • 200: Success
  
  POST /api/assessments/assessments/{id}/approve/
    Expected: 200 or 409
    Auth: admin only
    • 409: Invalid transition
    • 200: Success

REVIEWS:
  POST /api/reviews/reviews/
    Payload: {"assessment": 1, "comments": "Test review"}
    Expected: 201
    Auth: reviewer/admin only
  
  POST /api/reviews/reviews/{id}/decision/
    Payload: {"decision": "approved"}
    Expected: 200 or 409 (if already decided)
    Auth: reviewer/admin only

PERMISSION ERRORS (Expected 403):
  • Vendor tries to POST /api/vendors/vendors/
  • Non-admin tries to POST /api/templates/templates/
  • Non-vendor tries /api/assessments/assessments/{id}/submit/
  • Non-reviewer tries /api/reviews/reviews/{id}/decision/

STATE TRANSITION ERRORS (Expected 409):
  • Submit assessment already in 'submitted' status
  • Review assessment not in 'submitted' status
  • Approve assessment not in 'reviewed' status

CRITICAL: NO 500 ERRORS SHOULD OCCUR
""")

print("\n✅ All systems ready for P0 validation!")
print("=" * 80)
