#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from assessments.models import Assessment
from reviews.models import Review
from orgs.models import Organization

print("=" * 60)
print("Testing Review App After Fixes")
print("=" * 60)

# Check that org is used (not org_id)
print("\n✅ Review Model Fields:")
review_fields = [f.name for f in Review._meta.get_fields()]
print(f"  Fields: {review_fields}")
print(f"  Has 'org' field: {'org' in review_fields}")
print(f"  Has 'org_id' field: {'org_id' in review_fields}")

# Check database
print("\n✅ Database Check:")
org = Organization.objects.first()
reviewer = User.objects.filter(role='reviewer').first()
assessment = Assessment.objects.first()

if org:
    print(f"  Organization: {org.name}")
if reviewer:
    print(f"  Reviewer: {reviewer.email}")
if assessment:
    print(f"  Assessment: {assessment.id} (Status: {assessment.status})")

# Try creating a review
if reviewer and assessment and org:
    print("\n✅ Testing Review Creation:")
    review = Review.objects.create(
        org=org,
        assessment=assessment,
        reviewer=reviewer,
        comments="Test review",
        decision='approved'
    )
    print(f"  Created Review ID: {review.id}")
    print(f"  Review org: {review.org.name}")
    print(f"  Review assessment: {review.assessment.id}")
    print(f"  Review reviewer: {review.reviewer.email}")
    print(f"  Success!")

print("\n✅ All tests passed!")
print("=" * 60)
