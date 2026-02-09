#!/usr/bin/env python
"""Test responses and reviews endpoints to diagnose 400 errors."""
import os
import json
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User
from assessments.models import Assessment
from reviews.models import Review

# Wait a moment for server to be ready
time.sleep(2)

reviewer = User.objects.filter(role='reviewer').first()
assessment = Assessment.objects.first()

print("=" * 70)
print("Testing Responses & Reviews Endpoints")
print("=" * 70)

client = APIClient()
client.force_authenticate(user=reviewer)

# ===== TEST 1: Create Response =====
print("\n[TEST 1] POST /api/responses/responses/")
payload = {
    'assessment': assessment.id,
    'question_id': '00000000-0000-0000-0000-000000000000',
    'answer_text': 'Test answer'
}
resp = client.post('/api/responses/responses/', payload, format='json')
print(f'Status: {resp.status_code}')
if resp.status_code != 201:
    print(f'❌ Error: {json.dumps(resp.data, indent=2)}')
else:
    response_id = resp.data['id']
    print(f'✅ Response created: {response_id}')

# ===== TEST 2: Create Review =====
print("\n[TEST 2] POST /api/reviews/")
review_payload = {
    'assessment': assessment.id,
    'comments': 'Test review'
}
resp = client.post('/api/reviews/', review_payload, format='json')
print(f'Status: {resp.status_code}')
if resp.status_code != 201:
    print(f'❌ Error: {json.dumps(resp.data, indent=2)}')
else:
    review_id = resp.data['id']
    print(f'✅ Review created: {review_id}')
    
    # ===== TEST 3: Make Review Decision =====
    print("\n[TEST 3] POST /api/reviews/{}/decision/".format(review_id))
    decision_payload = {'decision': 'approved'}
    resp = client.post(f'/api/reviews/{review_id}/decision/', decision_payload, format='json')
    print(f'Status: {resp.status_code}')
    if resp.status_code != 200:
        print(f'❌ Error: {json.dumps(resp.data, indent=2)}')
    else:
        print(f'✅ Decision recorded: {resp.data}')

print("\n" + "=" * 70)
