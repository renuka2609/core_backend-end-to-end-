#!/usr/bin/env python
"""
Test script to verify all P0 conformance gate fixes
"""
import os
import sys
import django

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()
client = Client()

print("=" * 80)
print("P0 CONFORMANCE GATE TEST SUITE")
print("=" * 80)

# Test 1: RBAC Consistency (No hardcoded role strings)
print("\n✅ TEST 1: RBAC Consistency")
print("-" * 80)
from permissions.constants import Roles
print(f"Role constants are: {Roles.ALL_ROLES}")
print(f"Admin role: {Roles.ADMIN}")
print(f"Reviewer role: {Roles.REVIEWER}")
print(f"Vendor role: {Roles.VENDOR}")

# Verify User model uses constants
admin_user = User.objects.filter(role=Roles.ADMIN).first()
if admin_user:
    print(f"✓ Found admin user: {admin_user.username} with role: {admin_user.role}")
else:
    print(f"✗ No admin user found with role: {Roles.ADMIN}")

vendor_user = User.objects.filter(role=Roles.VENDOR).first()
if vendor_user:
    print(f"✓ Found vendor user: {vendor_user.username} with role: {vendor_user.role}")
else:
    print(f"✗ No vendor user found with role: {Roles.VENDOR}")

# Test 2: Org Linkage Stability
print("\n✅ TEST 2: Org Linkage Stability")
print("-" * 80)

# Login as vendor
login_response = client.post('/api/auth/login/', {
    'username': 'vendor',
    'password': 'vendor123'
})

if login_response.status_code == 200:
    print(f"✓ Vendor login successful")
    data = login_response.json()
    access_token = data.get('access')
    org_id = data.get('org_id')
    print(f"  - Org ID: {org_id}")
    print(f"  - Access token received: {access_token[:20]}...")
    
    # Try to create an assessment with this token
    from assessments.models import Assessment
    from vendors.models import Vendor
    from templates.models import Template
    from orgs.models import Organization
    
    org = Organization.objects.first()
    vendor_obj = Vendor.objects.filter(org=org).first()
    template = Template.objects.filter(org=org).first()
    
    if vendor_obj and template:
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        payload = {
            'vendor': vendor_obj.id,
            'template': template.id,
            'status': 'assigned'
        }
        create_response = client.post('/api/assessments/', payload, HTTP_AUTHORIZATION=f'Bearer {access_token}')
        if create_response.status_code in [201, 200]:
            print(f"✓ Assessment creation successful (status: {create_response.status_code})")
            assessment_data = create_response.json() if create_response.content else {}
            if isinstance(assessment_data, dict) and 'org' in assessment_data:
                print(f"  - Org attached: {assessment_data['org']}")
        else:
            print(f"✗ Assessment creation failed (status: {create_response.status_code})")
            print(f"  Response: {create_response.content[:200]}")
    else:
        print(f"✗ Could not find vendor or template for testing")
else:
    print(f"✗ Vendor login failed: {login_response.status_code}")
    print(f"  Response: {login_response.content[:200]}")

# Test 3: Workflow State Transitions (409 Conflict)
print("\n✅ TEST 3: Workflow State Transitions & 409 Conflict")
print("-" * 80)

from assessments.models import Assessment
assessments = Assessment.objects.all()
if assessments:
    test_assessment = assessments.first()
    print(f"Using assessment ID: {test_assessment.id} (current status: {test_assessment.status})")
    
    # Try invalid transition
    invalid_transition_from = test_assessment.STATUS_ASSIGNED
    invalid_transition_to = test_assessment.STATUS_APPROVED
    
    test_assessment.status = invalid_transition_from
    test_assessment.save()
    
    # Now try invalid transition
    from django.core.exceptions import ValidationError
    try:
        test_assessment.status = invalid_transition_to
        test_assessment.save()
        print(f"✗ Invalid transition was allowed (should have been 409)")
    except ValidationError as e:
        print(f"✓ Invalid transition was rejected with error:")
        print(f"  - {str(e)}")
    
    # Try valid transition
    test_assessment.status = test_assessment.STATUS_ASSIGNED
    test_assessment.save()
    test_assessment.status = test_assessment.STATUS_SUBMITTED
    try:
        test_assessment.save()
        print(f"✓ Valid transition (ASSIGNED -> SUBMITTED) allowed")
    except ValidationError as e:
        print(f"✗ Valid transition was rejected: {e}")

# Test 4: Audit Logging
print("\n✅ TEST 4: Audit Logging for Critical Actions")
print("-" * 80)

from audit.models import AuditLog

# Check for audit logs
recent_logs = AuditLog.objects.all().order_by('-timestamp')[:10]
if recent_logs:
    print(f"✓ Found {recent_logs.count()} audit log entries")
    for log in recent_logs:
        print(f"  - {log.action} (object: {log.object_id}, org: {log.org_id}) @ {log.timestamp}")
else:
    print(f"⚠ No audit logs found yet")

print("\n" + "=" * 80)
print("TEST SUITE COMPLETED")
print("=" * 80)
