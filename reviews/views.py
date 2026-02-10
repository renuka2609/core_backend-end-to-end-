from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
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
        # Resolve review (by review id or assessment id)
        try:
            review = self.get_object()
        except Exception:
            try:
                review = Review.objects.get(
                    assessment__id=pk,
                    org=self.request.user.org
                )
            except Review.DoesNotExist:
                return Response(
                    {"detail": "Review not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Normalize decision value
        data = dict(request.data)
        val = data.get('decision', '').lower()
        if val in ('approve', 'accepted', 'accept'):
            val = 'approved'
        if val in ('decline', 'deny'):
            val = 'rejected'
        data['decision'] = val

        serializer = ReviewDecisionSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        decision = serializer.validated_data['decision']

        # Prevent double decision
        if review.decision != "pending":
            return Response(
                {"detail": "review already decided"},
                status=status.HTTP_409_CONFLICT
            )

        # ============================
        # 🔴 NEW LOGIC STARTS HERE
        # ============================

        if decision == "approved":
            assessment = review.assessment

            # 1️⃣ Remediation check
            if hasattr(assessment, "remediation") and not assessment.remediation.is_approved:
                return Response(
                    {"detail": "Remediation pending. Cannot approve review."},
                    status=status.HTTP_409_CONFLICT
                )

            # 2️⃣ Call scoring service (with safe failure)
            try:
                from services.scoring import call_scoring_service
                scoring_response = call_scoring_service(
                    assessment.id,
                    timeout=5
                )
            except Exception:
                log_event(
                user=request.user,
                action="scoring_failed",
                object_id=assessment.id,
                metadata={"reason": "exception during scoring"}
    )
                return Response(
                    {"detail": "Scoring service failed. Approval not completed."},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            # 3️⃣ Persist scoring result (simple version)
            assessment.score = scoring_response.get("score")
            assessment.risk_level = scoring_response.get("risk_level")
            assessment.save()

            # Audit scoring
            log_event(
                user=request.user,
                action="scoring_triggered",
                object_id=assessment.id,
                metadata={"score": assessment.score}
            )

        # ============================
        # 🔴 NEW LOGIC ENDS HERE
        # ============================

        previous_decision = review.decision
        review.decision = decision
        review.save()

        # Audit review decision
        log_event(
            user=request.user,
            action="make_review_decision",
            object_id=review.id,
            metadata={
                "assessment_id": review.assessment.id,
                "previous_decision": previous_decision,
                "new_decision": decision
            }
        )

        return Response({"status": decision})
