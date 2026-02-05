from django.db import models
from django.conf import settings
from orgs.models import Organization



class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("status_change", "Status Change"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(max_length=50)
    object_id = models.IntegerField(null=True, blank=True)

    org = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.action} by {self.user} @ {self.timestamp}"



    