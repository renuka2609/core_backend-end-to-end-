from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from assessments.models import Assessment
from reviews.models import Review
from remediations.models import Remediation
from audit.models import AuditEvent
from permissions.rbac_policy import RBACPolicyHelper, RoleType
from .serializers import DashboardStatsSerializer, ActivityFeedSerializer

# Stats endpoint
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard stats filtered by user's organization and role."""
        user = request.user
        
        # Get user's organization
        user_org = getattr(user, 'org', None)
        if not user_org:
            return Response({"error": "User has no organization"}, status=400)
        
        # Get user's role
        user_role = RBACPolicyHelper.get_user_role(user)
        
        # Filter based on role
        if user_role == RoleType.ADMIN:
            # Admin sees all stats for organization
            assessment_qs = Assessment.objects.filter(org=user_org)
            review_qs = Review.objects.filter(org=user_org)
            remediation_qs = Remediation.objects.filter(org_id=user_org.id)
        elif user_role == RoleType.REVIEWER:
            # Reviewer sees submitted/reviewed/approved assessments
            assessment_qs = Assessment.objects.filter(
                org=user_org,
                status__in=['submitted', 'reviewed', 'approved']
            )
            review_qs = Review.objects.filter(org=user_org)
            remediation_qs = Remediation.objects.filter(org_id=user_org.id)
        elif user_role == RoleType.VENDOR:
            # Vendor sees organization-level assessment counts for their org
            remediation_qs = Remediation.objects.filter(org_id=user_org.id)
            assessment_qs = Assessment.objects.filter(org=user_org)
            review_qs = Review.objects.filter(org=user_org)
        else:
            # Viewer sees nothing sensitive
            assessment_qs = Assessment.objects.none()
            review_qs = Review.objects.none()
            remediation_qs = Remediation.objects.none()
        
        stats = {
            "total_assessments": assessment_qs.count(),
            "total_reviews": review_qs.count(),
            "total_remediations": remediation_qs.count(),
            "user_role": user_role.value if user_role else None,
        }
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

# Activity feed endpoint
class DashboardActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get activity feed filtered by user's organization and role."""
        user = request.user
        
        # Get user's organization
        user_org = getattr(user, 'org', None)
        if not user_org:
            return Response({"error": "User has no organization"}, status=400)
        
        # Get user's role
        user_role = RBACPolicyHelper.get_user_role(user)
        
        # Filter audit logs by organization
        logs_qs = AuditEvent.objects.filter(org=user_org).order_by('-created_at')[:50]
        
        # Additional filtering based on role
        if user_role == RoleType.VENDOR:
            # Vendor only sees logs for resources they can access
            from vendors.models import Vendor
            vendor = Vendor.objects.filter(org=user_org, users__in=[user]).first()
            if vendor:
                # Vendor sees logs for their assessments and remediations
                logs_qs = logs_qs.filter(
                    resource_type__in=['assessment', 'remediation']
                )
        
        feed = [
            {
                "actor": log.user.username if log.user else "System",
                "action": log.action,
                "entity": f"{log.resource_type}:{log.resource_id}" if log.resource_type else "Unknown",
                "timestamp": log.created_at,
            }
            for log in logs_qs
        ]
        serializer = ActivityFeedSerializer(feed, many=True)
        return Response(serializer.data)
