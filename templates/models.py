from django.db import models
from orgs.models import Organization

# Main Template
class Template(models.Model):
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="templates"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# Version of Template
class TemplateVersion(models.Model):
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name="versions"
    )
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.template.name} v{self.version}"


# Optional: Sections/Questions for Template
class TemplateSection(models.Model):
    template_version = models.ForeignKey(
        TemplateVersion,
        on_delete=models.CASCADE,
        related_name="sections"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class TemplateQuestion(models.Model):
    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    text = models.TextField()
    question_type = models.CharField(max_length=50, default="text")  # text, choice, etc.

    def __str__(self):
        return self.text
