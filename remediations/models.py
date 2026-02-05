from django.db import models
from assessments.models import Assessment

class Remediation(models.Model):

    STATUS = [
        ('open', 'Open'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]

    org_id = models.IntegerField()
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)

    issue = models.TextField()
    vendor_response = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='open')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Remediation {self.id}"
