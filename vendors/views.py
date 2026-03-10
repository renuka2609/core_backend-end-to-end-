from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Vendor
from .serializers import VendorSerializer
from permissions.rbac import IsAdmin
from permissions.tenant_guard import TenantAwareQueryGuardMixin


class VendorViewSet(TenantAwareQueryGuardMixin, viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    tenant_filter_field = 'org'

    def perform_create(self, serializer):
        # org automatically assign from logged in user
        serializer.save(org=self.request.user.org, created_by=self.request.user)
