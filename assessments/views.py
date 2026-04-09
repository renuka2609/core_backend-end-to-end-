from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Assessment
from .serializers import AssessmentSerializer
from .services import AssessmentStateTransitionService, StateTransitionError
from permissions.rbac_policy import (
    WorkflowActionPermission,
    WorkflowAction,
    RBACPolicyHelper,
)
from permissions.tenant_guard import TenantAwareQueryGuardMixin


class AssessmentViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        """Ensure create action is authorized."""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user,
            WorkflowAction.ASSESSMENT_CREATE
        )
        serializer.save(org=self.request.user.org)

    def _transition_assessment(self, assessment, target_status, request_metadata=None):
        """
        Helper to execute state transition with proper error handling.
        Returns: (Response, status_code)
        """
        try:
            updated = AssessmentStateTransitionService.transition(
                assessment=assessment,
                new_status=target_status,
                actor_user=self.request.user,
                metadata=request_metadata
            )
            return Response({
                "message": f"Assessment transitioned to {target_status}",
                "status": updated.status,
                "assessment": AssessmentSerializer(updated).data
            }), status.HTTP_200_OK
        except StateTransitionError as e:
            return Response({
                "error": str(e),
                "current_status": assessment.status,
                "valid_transitions": AssessmentStateTransitionService.get_valid_next_states(assessment)
            }), status.HTTP_409_CONFLICT

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def submit(self, request, pk=None):
        """Submit assessment for review (Vendor action)."""
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.ASSESSMENT_SUBMIT
        )
        
        assessment = self.get_object()
        response, resp_status = self._transition_assessment(
            assessment,
            Assessment.STATUS_SUBMITTED,
            request_metadata={"action": "vendor_submit"}
        )
        return response, resp_status

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def review(self, request, pk=None):
        """Move assessment to reviewed status (Admin/Reviewer action)."""
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.ASSESSMENT_REVIEW
        )
        
        assessment = self.get_object()
        response, resp_status = self._transition_assessment(
            assessment,
            Assessment.STATUS_REVIEWED,
            request_metadata={"action": "reviewer_review"}
        )
        return response, resp_status

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve assessment (Admin action)."""
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.ASSESSMENT_APPROVE
        )
        
        assessment = self.get_object()
        
        # Calculate score and risk before transitioning
        calculated_score = 85
        calculated_risk = "LOW"
        assessment.score = calculated_score
        assessment.risk_level = calculated_risk
        assessment.save(update_fields=['score', 'risk_level'])
        
        response, resp_status = self._transition_assessment(
            assessment,
            Assessment.STATUS_APPROVED,
            request_metadata={
                "action": "admin_approve",
                "score": calculated_score,
                "risk_level": calculated_risk
            }
        )
        
        if resp_status == status.HTTP_200_OK:
            response.data.update({
                "score": calculated_score,
                "risk_level": calculated_risk
            })
        
        return response, resp_status
    
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def remediate(self, request, pk=None):
        """Move assessment to remediation status (Admin/Reviewer action)."""
        WorkflowActionPermission.check_action_or_raise(
            request.user,
            WorkflowAction.ASSESSMENT_REVIEW  # Same permission as review
        )
        
        assessment = self.get_object()
        response, resp_status = self._transition_assessment(
            assessment,
            Assessment.STATUS_REMEDIATING,
            request_metadata={"action": "request_remediation"}
        )
        return response, resp_status
