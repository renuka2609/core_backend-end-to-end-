from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Template
from .serializers import TemplateSerializer
from permissions.tenant_guard import TenantAwareQueryGuardMixin


class TemplateViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    permission_classes = [IsAuthenticated]
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        serializer.save(org=self.request.user.org)
