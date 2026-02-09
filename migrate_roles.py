#!/usr/bin/env python
"""
Migrate old role values to new lowercase constants
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from permissions.constants import Roles

User = get_user_model()

# Mapping from old to new roles
role_mapping = {
    'ADMIN': Roles.ADMIN,
    'VENDOR': Roles.VENDOR,
    'REVIEWER': Roles.REVIEWER,
    'admin': Roles.ADMIN,
    'vendor': Roles.VENDOR,
    'reviewer': Roles.REVIEWER,
}

for user in User.objects.all():
    old_role = user.role
    new_role = role_mapping.get(old_role, old_role)
    if old_role != new_role:
        user.role = new_role
        user.save()
        print(f"Updated {user.username}: {old_role} -> {new_role}")
    else:
        print(f"✓ {user.username} already has correct role: {new_role}")

print("\n✅ All users migrated to new role constants!")

# Verify
print("\nVerifying migration:")
for user in User.objects.all():
    print(f"  - {user.username}: {user.role}")
