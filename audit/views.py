"""
Audit Event API Views

Read-only API for immutable append-only audit ledger.
Supports filtering by:
- resource_type and resource_id (to audit specific resources)
- user (to audit specific actor)
- date range (to audit events in time window)

All events are immutable once created - no updates or deletes allowed.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_datetime
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for audit events.
    
    Provides complete audit trail for compliance and forensics:
    - User actions and time stamps
    - Resource state changes (old vs new values)
    - Actor context (user, role, org)
    - Request metadata
    
    Immutable: Events cannot be modified or deleted after creation.
    Filtered by organization: Users only see audit logs for their org.
    """
    
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['resource_type', 'resource_id', 'user', 'action']
    ordering_fields = ['created_at', 'user', 'action']
    ordering = ['-created_at']
    search_fields = ['action', 'user__username', 'user__email']
    
    def get_queryset(self):
        """Filter audit events by user's organization."""
        user = self.request.user
        user_org = getattr(user, 'org', None)
        
        if not user_org:
            return AuditEvent.objects.none()
        
        return AuditEvent.objects.filter(org=user_org).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        List audit events with filtering and search.
        
        Query parameters:
        - resource_type: Filter by resource type (e.g., 'assessment')
        - resource_id: Filter by specific resource ID
        - user: Filter by user ID (actor)
        - action: Filter by action type
        - search: Full-text search on action, username, email
        - ordering: Sort by created_at, user, action (prefix with '-' for desc)
        """
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_resource(self, request):
        """
        Get audit trail for a specific resource.
        
        Query parameters:
        - resource_type: Required (e.g., 'assessment')
        - resource_id: Required (e.g., 1)
        
        Returns: Complete audit trail of all state changes for this resource
        """
        resource_type = request.query_params.get('resource_type')
        resource_id = request.query_params.get('resource_id')
        
        if not resource_type or not resource_id:
            return Response(
                {"error": "Missing required parameters: resource_type, resource_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            resource_id = int(resource_id)
        except ValueError:
            return Response(
                {"error": "resource_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = self.get_queryset().filter(
            resource_type=resource_type,
            resource_id=resource_id
        ).order_by('created_at')
        
        serializer = self.get_serializer(events, many=True)
        return Response({
            'resource_type': resource_type,
            'resource_id': resource_id,
            'audit_trail': serializer.data,
            'event_count': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_user(self, request):
        """
        Get all actions performed by a specific user.
        
        Query parameters:
        - user_id: Required (ID of user/actor)
        
        Returns: All audit events where this user was the actor
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response(
                {"error": "Missing required parameter: user_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_id = int(user_id)
        except ValueError:
            return Response(
                {"error": "user_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = self.get_queryset().filter(user_id=user_id).order_by('-created_at')
        
        serializer = self.get_serializer(events, many=True)
        return Response({
            'user_id': user_id,
            'action_count': len(serializer.data),
            'actions': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def by_date_range(self, request):
        """
        Get audit events within a date range.
        
        Query parameters:
        - start_date: ISO format (e.g., 2026-01-01T00:00:00Z)
        - end_date: ISO format (e.g., 2026-12-31T23:59:59Z)
        
        Returns: All audit events created between these dates
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            return Response(
                {"error": "Missing required parameters: start_date, end_date"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
            
            if not start_date or not end_date:
                raise ValueError("Invalid datetime format")
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid datetime format. Use ISO 8601 format."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = self.get_queryset().filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('created_at')
        
        serializer = self.get_serializer(events, many=True)
        return Response({
            'start_date': start_date_str,
            'end_date': end_date_str,
            'event_count': len(serializer.data),
            'events': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """Audit events are read-only - cannot be created via API."""
        return Response(
            {"error": "Audit events are immutable - cannot be created, updated, or deleted via API"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def update(self, request, *args, **kwargs):
        """Audit events are immutable - cannot be updated."""
        return Response(
            {"error": "Audit events are immutable - cannot be created, updated, or deleted via API"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Audit events are immutable - cannot be deleted."""
        return Response(
            {"error": "Audit events are immutable - cannot be created, updated, or deleted via API"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

