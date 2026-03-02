from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Vendor
from .serializers import VendorSerializer
from permissions.rbac import IsAdmin


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        # org automatically assign from logged in user
        serializer.save(created_by=self.request.user)
