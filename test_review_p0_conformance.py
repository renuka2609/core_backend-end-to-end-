#!/usr/bin/env python
"""
Comprehensive test demonstrating Review module fixes for P0 conformance.

This test validates that:
1. Review model uses org FK (not org_id INT field)
2. Review API endpoints work correctly
3. Audit logging is working for all review actions
4. RBAC permissions are enforced
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from users.models import User
from assessments.models import Assessment
from reviews.models import Review
from orgs.models import Organization
from audit.models import AuditLog
from permissions.constants import Roles

User = get_user_model()

print("\n" + "=" * 70)
print("P0 CONFORMANCE: Review Module Fixes")
print("=" * 70)

# ============================================================================
# TEST 1: Review Model Structure
# ============================================================================
print("\n[TEST 1] Review Model Structure")
print("-" * 70)

review_fields = {f.name for f in Review._meta.get_fields()}
assert 'org' in review_fields, "Review should have org FK field"
assert 'org_id' not in review_fields, "Review should NOT have org_id INT field"
assert 'updated_at' in review_fields, "Review should have updated_at"

print("✅ Review model structure is correct")
print("   - Has org (ForeignKey to Organization)")
print("   - Does NOT have org_id (IntegerField)")
print("   - Has updated_at (DateTimeField)")

# ============================================================================
# TEST 2: Review Creation - Org Linkage
# ============================================================================
print("\n[TEST 2] Review Creation - Org Linkage")
print("-" * 70)

org = Organization.objects.first()
reviewer = User.objects.get(email='reviewer@example.com')
assessment = Assessment.objects.first()

# Create review via API
client = APIClient()
client.force_authenticate(user=reviewer)

response = client.post('/api/reviews/', {
    'assessment': assessment.id,
    'comments': 'Assessment is complete and approved.',
}, format='json')

assert response.status_code == 201, f"Expected 201, got {response.status_code}"
review_data = response.data
review = Review.objects.get(id=review_data['id'])

assert review.org is not None, "Review org should not be None"
assert review.org.id == reviewer.org.id, "Review org should match reviewer's org"
assert review.assessment.id == assessment.id, "Review assessment should match"
assert review.reviewer.id == reviewer.id, "Review reviewer should match"

print("✅ Review creation with org linkage works correctly")
print(f"   - Review ID: {review.id}")
print(f"   - Org: {review.org.name}")
print(f"   - Assessment: {assessment.id}")
print(f"   - Reviewer: {reviewer.email}")

# ============================================================================
# TEST 3: Audit Logging
# ============================================================================
print("\n[TEST 3] Audit Logging for Review Actions")
print("-" * 70)

# Find the audit logs for this review
create_log = AuditLog.objects.get(
    action='create_review',
    object_id=review.id
)

assert create_log is not None, "Audit log for create_review should exist"
assert create_log.org is not None, "Audit log should have org context"
assert create_log.user.id == reviewer.id, "Audit log user should be reviewer"
assert create_log.metadata['assessment_id'] == assessment.id, "Metadata should include assessment_id"

print("✅ Audit logging for review creation works correctly")
print(f"   - Action: {create_log.action}")
print(f"   - User: {create_log.user.email}")
print(f"   - Org: {create_log.org.name}")
print(f"   - Object ID: {create_log.object_id}")
print(f"   - Metadata: {create_log.metadata}")

# ============================================================================
# TEST 4: Review Decision Endpoint - 409 Conflict Handling
# ============================================================================
print("\n[TEST 4] Review Decision Endpoint - 409 Conflict Handling")
print("-" * 70)

# Make a decision
response = client.post(
    f'/api/reviews/{review.id}/decision/',
    {'decision': 'approved'},
    format='json'
)

assert response.status_code == 200, f"Expected 200, got {response.status_code}"

# Try to make decision again on already-decided review
response = client.post(
    f'/api/reviews/{review.id}/decision/',
    {'decision': 'rejected'},
    format='json'
)

assert response.status_code == 409, f"Expected 409 for already-decided review, got {response.status_code}"
assert 'already decided' in response.data['detail'], "Should mention review already decided"

print("✅ Review decision endpoint enforces 409 Conflict for invalid transitions")
print(f"   - First decision: 200 OK (approved)")
print(f"   - Duplicate decision: 409 Conflict (already decided)")

# ============================================================================
# TEST 5: Audit Logging for Decision Action
# ============================================================================
print("\n[TEST 5] Audit Logging for Review Decision")
print("-" * 70)

decision_log = AuditLog.objects.get(
    action='make_review_decision',
    object_id=review.id
)

assert decision_log is not None, "Audit log for make_review_decision should exist"
assert decision_log.org is not None, "Decision audit log should have org"
assert decision_log.metadata['new_decision'] == 'approved', "Metadata should include new_decision"

print("✅ Audit logging for review decision works correctly")
print(f"   - Action: {decision_log.action}")
print(f"   - Org: {decision_log.org.name}")
print(f"   - Metadata: {decision_log.metadata}")

# ============================================================================
# TEST 6: RBAC Permission Check
# ============================================================================
print("\n[TEST 6] RBAC Permission Enforcement")
print("-" * 70)

vendor = User.objects.get(email='vendor@example.com')
vendor_client = APIClient()
vendor_client.force_authenticate(user=vendor)

# Vendor should not be able to make review decisions
response = vendor_client.post(
    f'/api/reviews/{review.id}/decision/',
    {'decision': 'approved'},
    format='json'
)

assert response.status_code == 403, f"Expected 403 for vendor decision, got {response.status_code}"

print("✅ RBAC enforcement prevents unauthorized review decisions")
print(f"   - Vendor (vendor@example.com) cannot make review decisions")
print(f"   - Response: 403 Forbidden")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("✅ ALL P0 CONFORMANCE TESTS PASSED")
print("=" * 70)
print("\nReview Module Fixes Confirmed:")
print("  1. ✅ Model uses org FK (not org_id INT field)")
print("  2. ✅ Org linkage is enforced in creation")
print("  3. ✅ Audit logging works for all review actions")
print("  4. ✅ Invalid transitions return 409 Conflict")
print("  5. ✅ RBAC permissions are enforced")
print("\n" + "=" * 70 + "\n")
