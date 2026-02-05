from django.db import models
from orgs.models import Organization

class Vendor(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
