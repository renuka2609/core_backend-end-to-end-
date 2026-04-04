from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from .models import Response
from .serializers import ResponseSerializer
from audit.services import log_event
from permissions.tenant_guard import TenantAwareQueryGuardMixin
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
    IsAdminOrVendor,
)


class IsAdminOrVendor(IsAuthenticated):
    """Allow Admin and Vendor users."""
    def has_permission(self, request, view):
        user = request.user
        if not super().has_permission(request, view):
            return False
        role = request.user.role.lower() if hasattr(request.user, 'role') else None
        return role in ['admin', 'vendor']


class ResponseViewSet(TenantAwareQueryGuardMixin, ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrVendor]
    tenant_filter_field = 'assessment__org'
    tenant_lookup_path = 'assessment__org'

    def perform_create(self, serializer):
        """Log response creation - check permissions"""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.RESPONSE_CREATE
        )
        
        response = serializer.save()
        log_event(
            user=self.request.user,
            action="response_created",
            object_id=response.id,
            metadata={
                "assessment_id": response.assessment.id,
                "question_id": str(response.question_id)
            }
        )

    def perform_update(self, serializer):
        """Log response update - check permissions"""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.RESPONSE_EDIT
        )
        
        response = serializer.save()
        log_event(
            user=self.request.user,
            action="response_updated",
            object_id=response.id,
            metadata={
                "assessment_id": response.assessment.id,
                "question_id": str(response.question_id)
            }
        )

    # Save draft = normal create/update already works

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        # Check workflow action permission
        WorkflowActionPermission.check_action_or_raise(
            request.user, WorkflowAction.RESPONSE_SUBMIT
        )
        
        obj = self.get_object()
        # return 409 if this response is already submitted
        if getattr(obj, "submitted", False):
            return DRFResponse({"error": "Already submitted"}, status=409)

        obj.submitted = True
        obj.save()

        log_event(
            user=request.user,
            action="response_submitted",
            object_id=obj.id,
            metadata={
                "assessment_id": obj.assessment.id,
                "question_id": str(obj.question_id)
            }
        )
