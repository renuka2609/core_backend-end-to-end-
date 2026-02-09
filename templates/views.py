from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .models import Template, TemplateVersion
from .serializers import TemplateSerializer, TemplateVersionSerializer
from permissions.rbac import CanCreateTemplate, CanCreateTemplateVersion
from audit.services import log_event


class TemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated, CanCreateTemplate]

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        if user and hasattr(user, "org") and user.org is not None:
            return Template.objects.filter(org=user.org)
        return Template.objects.none()

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        org = getattr(user, "org", None)
        if not org:
            raise PermissionDenied("User org is required")
        
        instance = serializer.save(org=org)
        # Log the creation
        log_event(user, "create_template", instance.id, {
            "template_name": instance.name,
            "org_id": org.id
        })


class TemplateVersionViewSet(viewsets.ModelViewSet):
    serializer_class = TemplateVersionSerializer
    permission_classes = [IsAuthenticated, CanCreateTemplateVersion]

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        if user and hasattr(user, "org") and user.org is not None:
            return TemplateVersion.objects.filter(template__org=user.org)
        return TemplateVersion.objects.none()

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        template = serializer.validated_data.get("template")
        if template and template.org != getattr(user, "org", None):
            raise PermissionDenied("Cannot create a version for a template outside your org")

        instance = serializer.save()
        # Log the creation
        log_event(user, "create_template_version", instance.id, {
            "template_id": template.id,
            "version": instance.version,
            "org_id": template.org.id
        })

