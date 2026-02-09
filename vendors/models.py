from django.db import models
from orgs.models import Organization

class Vendor(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    tier = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=32, default="active")

    def __str__(self):
        return self.name
