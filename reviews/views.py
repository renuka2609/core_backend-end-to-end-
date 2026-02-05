from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Review
from .serializers import ReviewSerializer, ReviewDecisionSerializer
from permissions.rbac import IsAdminOrReviewer
from audit.services import log_event


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReviewer]

    def get_queryset(self):
        return Review.objects.filter(org=self.request.user.org)

    def perform_create(self, serializer):
        review = serializer.save(
            reviewer=self.request.user,
            org=self.request.user.org
        )

        log_event(
            user=self.request.user,
            action="create_review",
            object_id=review.id,
            metadata={"assessment_id": review.assessment.id}
        )

    @action(detail=True, methods=['post'])
    def decision(self, request, pk=None):
        # Try to resolve the target review. Accept either a review id (pk)
        # or an assessment id (for convenience). This makes the endpoint more
        # forgiving for clients that only have the assessment id.
        review = None
        try:
            review = self.get_object()
        except Exception:
            # Try lookup by assessment id scoped to the user's org
            try:
                review = Review.objects.get(assessment__id=pk, org=self.request.user.org)
            except Review.DoesNotExist:
                return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Extract and normalize decision value from request
        data = dict(request.data)
        val = data.get('decision', '').lower()
        if val in ('approve', 'accepted', 'accept'):
            val = 'approved'
        if val in ('decline', 'deny'):
            val = 'rejected'
        data['decision'] = val

        # Validate input - provide helpful error message if validation fails
        serializer = ReviewDecisionSerializer(data=data)
        if not serializer.is_valid():
            # Log error details for easier debugging in server logs
            try:
                import logging
                logging.getLogger(__name__).warning('Review decision validation failed: %s', serializer.errors)
            except Exception:
                pass
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        decision = serializer.validated_data['decision']

        if review.decision != "pending":
            return Response({"detail": "review already decided"}, status=status.HTTP_409_CONFLICT)

        previous_decision = review.decision
        review.decision = decision
        review.save()

        log_event(
            user=request.user,
            action=f"make_review_decision",
            object_id=review.id,
            metadata={
                "assessment_id": review.assessment.id,
                "previous_decision": previous_decision,
                "new_decision": decision
            }
        )

        return Response({"status": decision})
