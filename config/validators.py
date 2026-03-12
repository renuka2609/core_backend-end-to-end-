"""
Request Validators for R-08 Input Validation

Provides schema validation decorators and utilities for DRF views.
"""

from typing import Type, Callable, Any
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
import functools
import logging

logger = logging.getLogger(__name__)


def validate_request_schema(serializer_class: Type[serializers.Serializer]):
    """
    Decorator to validate request data against a serializer schema.
    
    Usage:
        @validate_request_schema(MySerializer)
        def post(self, request):
            # request.validated_data is available
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            serializer = serializer_class(data=request.data)
            
            if not serializer.is_valid():
                raise ValidationError(serializer.errors)
            
            # Attach validated data to request
            request.validated_data = serializer.validated_data
            
            return func(self, request, *args, **kwargs)
        
        return wrapper
    return decorator


class SafeListSerializer(serializers.ListSerializer):
    """List serializer with safe error handling."""
    
    def to_representation(self, data):
        """Convert to safe representation."""
        try:
            return super().to_representation(data)
        except Exception as e:
            logger.exception("Error converting list to representation")
            return []


class InputSerializer(serializers.Serializer):
    """Base serializer with safe defaults."""
    
    class Meta:
        list_serializer_class = SafeListSerializer
    
    def to_representation(self, instance):
        """Remove None values from output."""
        ret = super().to_representation(instance)
        return {k: v for k, v in ret.items() if v is not None}


class AssessmentInputSerializer(InputSerializer):
    """Validate assessment creation/update requests."""
    
    vendor_id = serializers.IntegerField(required=True, min_value=1)
    template_id = serializers.IntegerField(required=True, min_value=1)
    status = serializers.CharField(required=False, max_length=50)
    
    def validate_status(self, value):
        """Ensure status is valid."""
        from assessments.models import Assessment
        valid_statuses = [s[0] for s in Assessment.STATUS]
        
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Valid options: {', '.join(valid_statuses)}"
            )
        
        return value


class VendorInputSerializer(InputSerializer):
    """Validate vendor creation/update requests."""
    
    name = serializers.CharField(required=True, max_length=255, min_length=1)
    email = serializers.EmailField(required=False, allow_blank=True)
    industry = serializers.CharField(required=False, max_length=255, allow_blank=True)
    tier = serializers.CharField(required=False, max_length=50, allow_blank=True)
    status = serializers.CharField(required=False, max_length=32, default="active")
    
    def validate_name(self, value):
        """Sanitize and validate vendor name."""
        value = value.strip()
        
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters")
        
        # Prevent SQL injection-like patterns
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        lower_val = value.lower()
        
        if any(char in lower_val for char in dangerous_chars):
            raise serializers.ValidationError("Name contains invalid characters")
        
        return value


class ReviewInputSerializer(InputSerializer):
    """Validate review creation/decision requests."""
    
    assessment_id = serializers.IntegerField(required=True, min_value=1)
    decision = serializers.CharField(required=True, max_length=50)
    comments = serializers.CharField(required=False, max_length=2000, allow_blank=True)
    
    def validate_decision(self, value):
        """Ensure decision is valid."""
        valid_decisions = ['approved', 'rejected', 'pending', 'remediation']
        
        if value.lower() not in valid_decisions:
            raise serializers.ValidationError(
                f"Invalid decision. Valid options: {', '.join(valid_decisions)}"
            )
        
        return value.lower()


class PaginationSerializer(InputSerializer):
    """Validate pagination parameters."""
    
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    
    def validate_page_size(self, value):
        """Limit page size."""
        max_size = 100
        if value > max_size:
            raise serializers.ValidationError(f"Page size cannot exceed {max_size}")
        return value


class DateRangeSerializer(InputSerializer):
    """Validate date range parameters."""
    
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    
    def validate(self, data):
        """Ensure end_date > start_date."""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("end_date must be after start_date")
        
        return data


def validate_file_upload(file_obj, max_size_mb=10, allowed_types=None):
    """
    Validate uploaded file.
    
    Args:
        file_obj: File object from request
        max_size_mb: Maximum file size in MB
        allowed_types: List of allowed MIME types
    
    Raises:
        ValidationError if file is invalid
    """
    if allowed_types is None:
        allowed_types = ['application/pdf', 'text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    
    # Check size
    max_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_bytes:
        raise ValidationError(
            f"File size exceeds {max_size_mb}MB limit"
        )
    
    # Check type
    if file_obj.content_type not in allowed_types:
        raise ValidationError(
            f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )


# Import all error envelope formatting
from config.middleware import StandardErrorEnvelope

__all__ = [
    'validate_request_schema',
    'InputSerializer',
    'AssessmentInputSerializer',
    'VendorInputSerializer',
    'ReviewInputSerializer',
    'PaginationSerializer',
    'DateRangeSerializer',
    'validate_file_upload',
    'StandardErrorEnvelope',
]
