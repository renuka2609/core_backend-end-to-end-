from rest_framework import viewsets, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Remediation
from .serializers import RemediationSerializer

from audit.services import log_event
from services.scoring_client import trigger_scoring


class RemediationViewSet(viewsets.ModelViewSet):
    queryset = Remediation.objects.all()
    serializer_class = RemediationSerializer

    def get_queryset(self):
        return Remediation.objects.filter(org_id=self.request.user.org_id)

    def perform_create(self, serializer):
        obj = serializer.save(org_id=self.request.user.org_id)

        log_event(
            user=self.request.user,
            action="remediation_created",
            obj=obj
        )

    # vendor responds
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        obj = self.get_object()

        if obj.status != "open":
            return Response({"error": "invalid state"}, status=409)

        obj.vendor_response = request.data.get("response", "")
        obj.status = "responded"
        obj.save()

        log_event(
            user=request.user,
            action="remediation_responded",
            obj=obj
        )

        return Response({"status": "responded"})

    # reviewer closes
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        obj = self.get_object()

        if obj.status != "responded":
            return Response({"error": "invalid state"}, status=409)

        obj.status = "closed"
        obj.save()

        trigger_scoring(obj.assessment.id)

        log_event(
            user=request.user,
            action="remediation_closed",
            obj=obj
        )

        return Response({"status": "closed"})
