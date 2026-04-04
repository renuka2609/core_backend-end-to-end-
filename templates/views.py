from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Template
from .serializers import TemplateSerializer
from permissions.tenant_guard import TenantAwareQueryGuardMixin
from permissions.rbac_policy import (
    IsAdmin,
    WorkflowActionPermission,
    WorkflowAction,
)


class TemplateViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        """Create template with permission check."""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.TEMPLATE_CREATE
        )
        
        serializer.save(org=self.request.user.org)
