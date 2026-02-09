from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from .models import Assessment
from .serializers import AssessmentSerializer
from permissions.rbac import CanSubmitAssessment, CanReviewAssessment, CanApproveAssessment
from audit.services import log_event


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [
        IsAuthenticated, 
        CanSubmitAssessment, 
        CanReviewAssessment, 
        CanApproveAssessment
    ]

    def get_queryset(self):
        """
        Only show assessments of user's org
        """
        user = getattr(self.request, "user", None)
        if user and hasattr(user, "org"):
            return Assessment.objects.filter(org=user.org)
        return Assessment.objects.none()

    def perform_create(self, serializer):
        """
        Auto attach org and log the creation
        """
        user = self.request.user
        org = user.org
        
        if not org:
            raise ValidationError("User organization is required to create assessments")
        
        instance = serializer.save(org=org)
        
        # Log the creation
        log_event(user, "create_assessment", instance.id, {
            "vendor_id": instance.vendor.id,
            "template_id": instance.template.id,
            "status": instance.status,
            "org_id": org.id
        })

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Vendor submits assessment (ASSIGNED -> SUBMITTED)
        """
        assessment = self.get_object()
        user = request.user
        
        # Validate status transition
        is_valid, error_msg = assessment.can_transition_to(Assessment.STATUS_SUBMITTED)
        if not is_valid:
            return Response(
                {"detail": error_msg},
                status=status.HTTP_409_CONFLICT
            )
        
        assessment.status = Assessment.STATUS_SUBMITTED
        try:
            assessment.save()
        except DjangoValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        
        # Log the submission
        log_event(user, "submit_assessment", assessment.id, {
            "previous_status": Assessment.STATUS_ASSIGNED,
            "new_status": Assessment.STATUS_SUBMITTED,
            "org_id": assessment.org.id
        })
        
        return Response(
            AssessmentSerializer(assessment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """
        Reviewer reviews assessment (SUBMITTED -> REVIEWED)
        """
        assessment = self.get_object()
        user = request.user
        
        # Validate status transition
        is_valid, error_msg = assessment.can_transition_to(Assessment.STATUS_REVIEWED)
        if not is_valid:
            return Response(
                {"detail": error_msg},
                status=status.HTTP_409_CONFLICT
            )
        
        assessment.status = Assessment.STATUS_REVIEWED
        try:
            assessment.save()
        except DjangoValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        
        # Log the review
        log_event(user, "review_assessment", assessment.id, {
            "previous_status": Assessment.STATUS_SUBMITTED,
            "new_status": Assessment.STATUS_REVIEWED,
            "org_id": assessment.org.id
        })
        
        return Response(
            AssessmentSerializer(assessment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Admin approves assessment (REVIEWED -> APPROVED)
        """
        assessment = self.get_object()
        user = request.user
        
        # Validate status transition
        is_valid, error_msg = assessment.can_transition_to(Assessment.STATUS_APPROVED)
        if not is_valid:
            return Response(
                {"detail": error_msg},
                status=status.HTTP_409_CONFLICT
            )
        
        assessment.status = Assessment.STATUS_APPROVED
        try:
            assessment.save()
        except DjangoValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        
        # Log the approval
        log_event(user, "approve_assessment", assessment.id, {
            "previous_status": Assessment.STATUS_REVIEWED,
            "new_status": Assessment.STATUS_APPROVED,
            "org_id": assessment.org.id
        })
        
        return Response(
            AssessmentSerializer(assessment).data,
            status=status.HTTP_201_CREATED
        )
