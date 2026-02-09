#!/usr/bin/env python
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from rest_framework.test import APIClient
from users.models import User
from assessments.models import Assessment
from reviews.models import Review
from orgs.models import Organization
from rest_framework_simplejwt.tokens import RefreshToken

print("=" * 60)
print("Testing Review API Endpoint")
print("=" * 60)

# Setup
org = Organization.objects.first()
reviewer = User.objects.filter(role='reviewer').first()
admin = User.objects.filter(role='admin').first()
assessment = Assessment.objects.first()

if not reviewer:
    print("❌ No reviewer found")
    sys.exit(1)

if not admin:
    print("❌ No admin found")
    sys.exit(1)

if not assessment:
    print("❌ No assessment found")
    sys.exit(1)

# Create JWT token for reviewer
refresh = RefreshToken.for_user(reviewer)
access_token = str(refresh.access_token)

print(f"\n✅ Setup:")
print(f"  Organization: {org.name}")
print(f"  Reviewer: {reviewer.email}")
print(f"  Admin: {admin.email}")
print(f"  Assessment: {assessment.id} (Status: {assessment.status})")

# Test API
client = APIClient()
client.force_authenticate(user=reviewer)

print(f"\n✅ Testing Review Creation Endpoint:")

# Create review
review_data = {
    "assessment": assessment.id,
    "comments": "This assessment looks good and is ready for approval.",
}

response = client.post('/api/reviews/', review_data, format='json')
print(f"  POST /api/reviews/")
print(f"  Status Code: {response.status_code}")
print(f"  Response: {response.data if response.status_code == 201 else response.data}")

if response.status_code == 201:
    print(f"  ✅ Review created successfully!")
    review_id = response.data.get('id')
    
    # Test decision endpoint
    print(f"\n✅ Testing Review Decision Endpoint:")
    decision_data = {"decision": "approved"}
    response = client.post(f'/api/reviews/{review_id}/decision/', decision_data, format='json')
    print(f"  POST /api/reviews/{review_id}/decision/")
    print(f"  Status Code: {response.status_code}")
    print(f"  Response: {response.data}")
    
    if response.status_code == 200:
        print(f"  ✅ Decision recorded successfully!")
    else:
        print(f"  ❌ Decision failed")
else:
    print(f"  ❌ Review creation failed")

print("\n" + "=" * 60)
