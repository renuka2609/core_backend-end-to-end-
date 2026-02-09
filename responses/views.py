from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from .models import Response
from .serializers import ResponseSerializer
from audit.services import log_event


class ResponseViewSet(ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show responses for user's org"""
        user = self.request.user
        return Response.objects.filter(assessment__org=user.org)

    def perform_create(self, serializer):
        """Log response creation"""
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
        """Log response update"""
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
