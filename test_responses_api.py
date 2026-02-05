#!/usr/bin/env python
import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from users.models import User
from assessments.models import Assessment
from responses.models import Response

reviewer = User.objects.filter(role='reviewer').first()
assessment = Assessment.objects.first()

client = APIClient()
client.force_authenticate(user=reviewer)

payload = {
    'assessment': assessment.id,
    'question_id': '00000000-0000-0000-0000-000000000000',
    'answer_text': 'Test answer'
}

resp = client.post('/api/responses/responses/', payload, format='json')
print(f'Status: {resp.status_code}')
print(f'Response: {json.dumps(resp.data, indent=2)}')

# If successful, test the submit endpoint
if resp.status_code == 201:
    response_id = resp.data['id']
    print(f'\n✅ Response created: {response_id}')
    
    submit_resp = client.post(f'/api/responses/responses/{response_id}/submit/', {}, format='json')
    print(f'Submit Status: {submit_resp.status_code}')
    print(f'Submit Response: {submit_resp.data}')
