from django.db import models
from django.conf import settings
from assessments.models import Assessment


class Evidence(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question_id = models.IntegerField()

    file = models.FileField(upload_to="evidence/")
    file_type = models.CharField(max_length=50)

    expiry_date = models.DateField(null=True, blank=True)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence {self.id}"
