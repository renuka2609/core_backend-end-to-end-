"""
Audit Event Serializers

Serializers for the immutable append-only audit ledger.
"""

from rest_framework import serializers
from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditEvent - read-only to maintain immutability.
    
    Exposes all audit trail information:
    - actor (user who performed action)
    - action (what was done)
    - resource tracking (type, id for filtering by resource)
    - metadata (old/new values, context)
    - timestamp
    """
    
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'user',
            'user_details',
            'action',
            'resource_type',
            'resource_id',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_details(self, obj):
        """Include user details for better audit readability."""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'role': getattr(obj.user, 'role', None),
        }
