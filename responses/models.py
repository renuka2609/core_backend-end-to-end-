from django.db import models
from assessments.models import Assessment

class Response(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    question_id = models.UUIDField()
    answer_text = models.TextField(blank=True)
    submitted = models.BooleanField(default=False)
