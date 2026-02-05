#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from audit.models import AuditLog

print("=" * 60)
print("Audit Logs After Review Actions")
print("=" * 60)

logs = AuditLog.objects.all().order_by('-timestamp')[:5]

for log in logs:
    print(f"\n✅ Log {log.id}:")
    print(f"  Action: {log.action}")
    print(f"  User: {log.user.email}")
    print(f"  Org: {log.org.name if log.org else 'None'}")
    print(f"  Object ID: {log.object_id}")
    print(f"  Metadata: {log.metadata}")
    print(f"  Created: {log.timestamp}")

print("\n" + "=" * 60)
print(f"✅ Total audit logs: {AuditLog.objects.count()}")
print("=" * 60)
