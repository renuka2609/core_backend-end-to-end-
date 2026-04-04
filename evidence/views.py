from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import Evidence
from .serializers import EvidenceSerializer
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


class EvidenceViewSet(TenantAwareQueryGuardMixin, ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrVendor]
    tenant_filter_field = 'assessment__org'
    tenant_lookup_path = 'assessment__org'

    def perform_create(self, serializer):
        """Log evidence creation - check permissions"""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.EVIDENCE_CREATE
        )
        
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
        """Log evidence update - check permissions"""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.EVIDENCE_EDIT
        )
        
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
        """Log evidence deletion - check permissions"""
        WorkflowActionPermission.check_action_or_raise(
            self.request.user, WorkflowAction.EVIDENCE_DELETE
        )
        
        eid = instance.id
        assessment_id = instance.assessment.id
        instance.delete()
        log_event(
            user=self.request.user,
            action="evidence_deleted",
            object_id=eid,
            metadata={"assessment_id": assessment_id}
        )
