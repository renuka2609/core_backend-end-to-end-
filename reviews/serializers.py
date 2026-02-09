from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'org', 'assessment', 'reviewer', 'comments', 'decision', 'created_at', 'updated_at']
        read_only_fields = ['reviewer', 'org', 'decision', 'created_at', 'updated_at']


class ReviewDecisionSerializer(serializers.Serializer):
    """Serializer for the review decision action."""
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])

