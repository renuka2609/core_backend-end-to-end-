from django.contrib.auth.models import AbstractUser
from django.db import models
from orgs.models import Organization
from permissions.constants import Roles


class User(AbstractUser):
    ROLE_CHOICES = Roles.CHOICES
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=Roles.ADMIN)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)

    def __str__(self):
        return self.username

