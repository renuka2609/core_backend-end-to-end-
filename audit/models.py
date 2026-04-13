from django.db import models
from django.conf import settings
from orgs.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()

class AuditEvent(models.Model):
    """
    Immutable append-only audit ledger for all state-changing operations.
    
    Each write action is logged with:
    - actor (user performing action)
    - action (what was done)
    - resource tracking (type and id)
    - metadata (old/new values and context)
    - timestamp (auto)
    - organization (for tenant isolation)
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Organization that owns this audit event"
    )
    action = models.CharField(
        max_length=255,
        help_text="Action performed (e.g., 'assessment_transitioned: assigned → submitted')"
    )
    resource_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Type of resource affected (e.g., 'assessment', 'review', 'vendor')"
    )
    resource_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of resource affected"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context: old_value, new_value, actor details, request metadata"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource_type', 'resource_id', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        if self.resource_type and self.resource_id:
            return f"{self.user} - {self.action} [{self.resource_type}:{self.resource_id}]"
        return f"{self.user} - {self.action}"


# Backward compatibility alias
AuditLog = AuditEvent