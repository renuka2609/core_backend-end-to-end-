from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from assessments.models import Assessment
from reviews.models import Review
from remediations.models import Remediation
from audit.models import AuditLog
from .serializers import DashboardStatsSerializer, ActivityFeedSerializer

# Stats endpoint
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard stats filtered by user's organization."""
        user = request.user
        
        # Get user's organization
        user_org = getattr(user, 'org', None)
        if not user_org:
            return Response({"error": "User has no organization"}, status=400)
        
        stats = {
            "total_assessments": Assessment.objects.filter(org=user_org).count(),
            "total_reviews": Review.objects.filter(org=user_org).count(),
            "total_remediations": Remediation.objects.filter(org_id=user_org.id).count(),
        }
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

# Activity feed endpoint
class DashboardActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get activity feed filtered by user's organization."""
        user = request.user
        
        # Get user's organization
        user_org = getattr(user, 'org', None)
        if not user_org:
            return Response({"error": "User has no organization"}, status=400)
        
        logs = AuditLog.objects.filter(org=user_org).order_by('-timestamp')[:50]
        feed = [
            {
                "actor": log.user.username if log.user else "System",
                "action": log.action,
                "entity": log.entity if hasattr(log, 'entity') else "Unknown",
                "timestamp": log.timestamp if hasattr(log, 'timestamp') else None,
            }
            for log in logs
        ]
        serializer = ActivityFeedSerializer(feed, many=True)
        return Response(serializer.data)
