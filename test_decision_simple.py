#!/usr/bin/env python
"""Test review decision with proper error reporting."""
import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User
from assessments.models import Assessment
from reviews.models import Review

reviewer = User.objects.filter(role='reviewer').first()
assessment = Assessment.objects.first()

print("=" * 70)
print("Testing Review Decision Endpoint")
print("=" * 70)

client = APIClient()
client.force_authenticate(user=reviewer)

# Create a review
print("\n[1] Creating review...")
resp = client.post('/api/reviews/', {
    'assessment': assessment.id,
    'comments': 'Test review'
}, format='json')
print(f'Status: {resp.status_code}')
review_id = resp.data['id']
print(f'Review ID: {review_id}')

# Try decision with valid data
print(f"\n[2] Making decision with valid data...")
resp = client.post(f'/api/reviews/{review_id}/decision/', {
    'decision': 'approved'
}, format='json')
print(f'Status: {resp.status_code}')
print(f'Response: {json.dumps(resp.data, indent=2)}')

if resp.status_code == 200:
    print("✅ SUCCESS")
elif resp.status_code == 400:
    print("❌ 400 Bad Request - validation error")
    print(f"Error details: {resp.data}")
