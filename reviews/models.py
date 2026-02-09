from django.db import models
from django.conf import settings
from assessments.models import Assessment
from orgs.models import Organization


class Review(models.Model):
    DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    comments = models.TextField(blank=True, null=True)
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.id} - {self.decision}"
