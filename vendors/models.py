from django.db import models
from accounts.models import Tenant
from orgs.models import Organization

class Vendor(models.Model):
    """
    Vendor model for tracking third-party vendors.
    
    Related to:
    - Organization: Vendors belong to an org
    - Tenant: Vendor also linked to tenant for backward compatibility
    """
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='vendors')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    
    industry = models.CharField(max_length=255, blank=True)
    tier = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=32, default="active")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['org', '-created_at']),
        ]

    def __str__(self):
        return self.name
