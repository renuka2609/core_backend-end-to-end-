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
        tenant_id = request.user.tenant_id
        stats = {
            "total_assessments": Assessment.objects.filter(tenant_id=tenant_id).count(),
            "total_reviews": Review.objects.filter(tenant_id=tenant_id).count(),
            "total_remediations": Remediation.objects.filter(tenant_id=tenant_id).count(),
        }
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

# Activity feed endpoint
class DashboardActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        logs = AuditLog.objects.filter(tenant_id=tenant_id).order_by('-timestamp')[:50]
        feed = [
            {
                "actor": log.user.username,
                "action": log.action,
                "entity": log.entity,
                "timestamp": log.timestamp,
            }
            for log in logs
        ]
        serializer = ActivityFeedSerializer(feed, many=True)
        return Response(serializer.data)
