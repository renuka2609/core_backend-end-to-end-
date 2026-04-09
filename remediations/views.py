from rest_framework import viewsets, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Remediation
from .serializers import RemediationSerializer

from audit.services import log_event
from services.scoring_client import trigger_scoring
from permissions.tenant_guard import TenantAwareQueryGuardMixin
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
    IsAdminOrReviewer,
    IsVendor,
    RBACPolicyHelper,
)


class RemediationViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Remediation.objects.all()
    serializer_class = RemediationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReviewer]  # FIXED: Critical - was missing!
    tenant_filter_field = 'org_id'

    def perform_create(self, serializer):
        """Create remediation with permission check."""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.REMEDIATION_CREATE
        )
        
        obj = serializer.save(org_id=self.request.user.org_id)

        log_event(
            user=self.request.user,
            action="remediation_created",
            resource_type="remediation",
            resource_id=obj.id,
            metadata={
                "assessment_id": obj.assessment_id,
                "status": obj.status,
            }
        )

    # vendor responds
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsVendor])
    def respond(self, request, pk=None):
        # Check workflow action permission
        WorkflowActionPermission.check_action_or_raise(
            request.user, WorkflowAction.REMEDIATION_RESPOND
        )
        
        obj = self.get_object()

        if obj.status != "open":
            return Response({"error": "invalid state"}, status=409)

        obj.vendor_response = request.data.get("response", "")
        obj.status = "responded"
        obj.save()

        log_event(
            user=request.user,
            action="remediation_responded",
            resource_type="remediation",
            resource_id=obj.id,
            metadata={
                "assessment_id": obj.assessment_id,
                "status": obj.status,
            }
        )

        return Response({"status": "responded"})

    # reviewer closes
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrReviewer])
    def close(self, request, pk=None):
        # Check workflow action permission
        WorkflowActionPermission.check_action_or_raise(
            request.user, WorkflowAction.REMEDIATION_CLOSE
        )
        
        obj = self.get_object()

        if obj.status != "responded":
            return Response({"error": "invalid state"}, status=409)

        obj.status = "closed"
        obj.save()

        trigger_scoring(obj.assessment.id)

        log_event(
            user=request.user,
            action="remediation_closed",
            resource_type="remediation",
            resource_id=obj.id,
            metadata={
                "assessment_id": obj.assessment_id,
                "status": obj.status,
            }
        )

        return Response({"status": "closed"})
