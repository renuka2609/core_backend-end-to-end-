from rest_framework import serializers

class DashboardStatsSerializer(serializers.Serializer):
    total_assessments = serializers.IntegerField()
    total_reviews = serializers.IntegerField()
    total_remediations = serializers.IntegerField()

class ActivityFeedSerializer(serializers.Serializer):
    actor = serializers.CharField()
    action = serializers.CharField()
    entity = serializers.CharField()
    timestamp = serializers.DateTimeField()
