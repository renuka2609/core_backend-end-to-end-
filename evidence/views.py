from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import Evidence
from .serializers import EvidenceSerializer
from audit.services import log_event


class EvidenceViewSet(ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show evidence for user's org"""
        user = self.request.user
        return Evidence.objects.filter(assessment__org=user.org)

    def perform_create(self, serializer):
        """Log evidence creation"""
        evidence = serializer.save(uploaded_by=self.request.user)
        log_event(
            user=self.request.user,
            action="evidence_created",
            object_id=evidence.id,
            metadata={
                "assessment_id": evidence.assessment.id,
                "file_name": evidence.file.name if evidence.file else None
            }
        )

    def perform_update(self, serializer):
        """Log evidence update"""
        evidence = serializer.save()
        log_event(
            user=self.request.user,
            action="evidence_updated",
            object_id=evidence.id,
            metadata={
                "assessment_id": evidence.assessment.id,
                "file_name": evidence.file.name if evidence.file else None
            }
        )

    def perform_destroy(self, instance):
        """Log evidence deletion"""
        eid = instance.id
        assessment_id = instance.assessment.id
        instance.delete()
        log_event(
            user=self.request.user,
            action="evidence_deleted",
            object_id=eid,
            metadata={"assessment_id": assessment_id}
        )
