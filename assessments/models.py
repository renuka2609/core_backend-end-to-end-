from django.db import models
from django.core.exceptions import ValidationError
from orgs.models import Organization
from vendors.models import Vendor
from templates.models import Template


class Assessment(models.Model):
    STATUS_ASSIGNED = "assigned"
    STATUS_SUBMITTED = "submitted"
    STATUS_REVIEWED = "reviewed"
    STATUS_APPROVED = "approved"
    
    STATUS = [
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_APPROVED, "Approved"),
    ]
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        STATUS_ASSIGNED: [STATUS_SUBMITTED],  # Vendor submits
        STATUS_SUBMITTED: [STATUS_REVIEWED],  # Reviewer reviews
        STATUS_REVIEWED: [STATUS_APPROVED],   # Admin approves
        STATUS_APPROVED: [],  # Final state
    }

    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default=STATUS_ASSIGNED)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Assessment {self.id} - {self.vendor.name} ({self.status})"
    
    def is_valid_transition(self, new_status: str) -> bool:
        """Check if transition from current status to new_status is valid"""
        if self.status not in self.VALID_TRANSITIONS:
            return False
        return new_status in self.VALID_TRANSITIONS[self.status]
    
    def can_transition_to(self, new_status: str) -> tuple[bool, str]:
        """
        Validate if the assessment can transition to a new status.
        Returns: (is_valid, error_message)
        """
        if new_status == self.status:
            return True, ""
        
        if not self.is_valid_transition(new_status):
            valid_transitions = self.VALID_TRANSITIONS.get(self.status, [])
            return False, (
                f"Cannot transition from '{self.status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(valid_transitions) if valid_transitions else 'none'}"
            )
        
        return True, ""
    
    def save(self, *args, **kwargs):
        """Validate state transitions before saving"""
        if self.pk:  # If updating (not creating)
            original = Assessment.objects.get(pk=self.pk)
            if original.status != self.status:
                is_valid, error_msg = self.can_transition_to(self.status)
                if not is_valid:
                    raise ValidationError(error_msg)
        super().save(*args, **kwargs)


