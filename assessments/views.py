from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Assessment
from .serializers import AssessmentSerializer
from permissions.rbac import IsAdminOrReviewer, IsVendor
from permissions.tenant_guard import TenantAwareQueryGuardMixin


class AssessmentViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_field = 'org'

    @action(detail=True, methods=["post"], permission_classes=[IsVendor])
    def submit(self, request, pk=None):
        assessment = self.get_object()
        assessment.status = "submitted"
        assessment.save()
        return Response({"message": "Assessment submitted"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrReviewer])
    def review(self, request, pk=None):
        assessment = self.get_object()
        assessment.status = "under_review"
        assessment.save()
        return Response({"message": "Assessment under review"})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrReviewer])
    def approve(self, request, pk=None):
        assessment = self.get_object()

        calculated_score = 85
        calculated_risk = "LOW"

        assessment.status = "approved"   # 🔴 ADD THIS
        assessment.score = calculated_score
        assessment.risk_level = calculated_risk
        assessment.save()

        return Response({
        "message": "Assessment approved",
        "score": calculated_score,
        "risk_level": calculated_risk
    })

