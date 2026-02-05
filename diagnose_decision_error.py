#!/usr/bin/env python
"""Diagnose review decision endpoint 400 errors."""
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
admin = User.objects.filter(role='admin').first()
assessment = Assessment.objects.first()

print("=" * 70)
print("Diagnosing Review Decision 400 Errors")
print("=" * 70)

client = APIClient()
client.force_authenticate(user=reviewer)

# Create a fresh review
print("\n[STEP 1] Creating a review...")
review_payload = {
    'assessment': assessment.id,
    'comments': 'Ready for decision'
}
resp = client.post('/api/reviews/', review_payload, format='json')
print(f'Status: {resp.status_code}')
if resp.status_code != 201:
    print(f'❌ Failed to create review: {json.dumps(resp.data, indent=2)}')
else:
    review_id = resp.data['id']
    print(f'✅ Review {review_id} created')
    
    # Try to make decision
    print(f"\n[STEP 2] Making decision on review {review_id}...")
    
    # Test with different payload formats
    test_payloads = [
        {'decision': 'approved'},
        {'decision': 'rejected'},
        {},  # Empty to see what error we get
    ]
    
    for payload in test_payloads:
        print(f"\n  Testing payload: {payload}")
        resp = client.post(f'/api/reviews/{review_id}/decision/', payload, format='json')
        print(f'  Status: {resp.status_code}')
        print(f'  Response: {json.dumps(resp.data, indent=2)}')
        
        # Only test subsequent payloads if first one fails
        if resp.status_code in [200, 409]:
            break

print("\n" + "=" * 70)
