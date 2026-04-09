from requests import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from urllib3 import request
from .models import Vendor
from .serializers import VendorSerializer
from permissions.rbac_policy import (
    IsAdmin,
    WorkflowActionPermission,
    WorkflowAction,
)
from permissions.tenant_guard import TenantAwareQueryGuardMixin


class VendorViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        """Ensure vendor creation is authorized."""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.VENDOR_CREATE
        )
        # Assign org and creator from authenticated user
        serializer.save(org=self.request.user.org, created_by=self.request.user)