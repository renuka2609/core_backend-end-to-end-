from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Review
from .serializers import ReviewSerializer
from permissions.rbac import IsReviewer
from permissions.tenant_guard import TenantAwareQueryGuardMixin


class ReviewViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewer]
    tenant_filter_field = 'org'

    @action(detail=True, methods=["post"])
    def decision(self, request, pk=None):
        review = self.get_object()
        decision = request.data.get("decision")

        review.status = decision
        review.save()

        return Response({"message": "Decision updated"})
