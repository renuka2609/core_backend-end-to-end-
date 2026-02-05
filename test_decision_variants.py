#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()

from rest_framework.test import APIClient
from users.models import User
from assessments.models import Assessment

reviewer = User.objects.filter(role='reviewer').first()
assessment = Assessment.objects.first()
client = APIClient(); client.force_authenticate(user=reviewer)

variants = [
    {'decision':'APPROVED'},
    {'decision':'approve'},
    {'decision':'Accept'},
    {'decision':'ReJeCT'},
    {},
]

for v in variants:
    resp = client.post('/api/reviews/', {'assessment': assessment.id, 'comments':'vtest'}, format='json')
    rid = resp.data['id']
    r = client.post(f'/api/reviews/{rid}/decision/', v, format='json')
    print('payload=', v, 'status=', r.status_code, 'resp=', r.data)
