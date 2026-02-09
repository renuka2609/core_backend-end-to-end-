from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from .models import Vendor
from .serializers import VendorSerializer
from .permissions import CanCreateVendor
from audit.services import log_event


class VendorViewSet(ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated, CanCreateVendor]

    # ✅ REQUIRED for router basename auto-detect
    queryset = Vendor.objects.all()

    # -------------------------
    # Tenant + Filters
    # -------------------------
    def get_queryset(self):
        user = self.request.user

        # safety guard
        if not user.is_authenticated or not hasattr(user, "org"):
            return Vendor.objects.none()

        qs = Vendor.objects.filter(org=user.org)

        # filters
        status_param = self.request.query_params.get("status")
        tier = self.request.query_params.get("tier")
        search = self.request.query_params.get("search")

        if status_param:
            qs = qs.filter(status=status_param)

        if tier:
            qs = qs.filter(tier=tier)

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search)
            )

        return qs

    # -------------------------
    # Create with org attach + audit
    # -------------------------
    def perform_create(self, serializer):
        user = self.request.user

        if not user or not user.is_authenticated or not hasattr(user, "org"):
            raise ValidationError({"org": "Authenticated user must belong to an organization."})

        vendor = serializer.save(org=user.org)

        log_event(
            user=user,
            action="vendor_created",
            object_id=vendor.id
        )

    # -------------------------
    # Update with audit
    # -------------------------
    def perform_update(self, serializer):
        vendor = serializer.save()

        log_event(
            user=self.request.user,
            action="vendor_updated",
            object_id=vendor.id
        )

    # -------------------------
    # Delete with audit
    # -------------------------
    def perform_destroy(self, instance):
        vid = instance.id
        instance.delete()

        log_event(
            user=self.request.user,
            action="vendor_deleted",
            object_id=vid
        )

    # -------------------------
    # Vendor Status Transition
    # -------------------------
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        vendor = self.get_object()
        new_status = request.data.get("status")

        allowed_status = ["active", "inactive", "blocked"]

        if new_status not in allowed_status:
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        vendor.status = new_status
        vendor.save()

        log_event(
            user=request.user,
            action="vendor_status_changed",
            object_id=vendor.id
        )

        return Response({
            "message": "Status updated",
            "new_status": new_status
        })
