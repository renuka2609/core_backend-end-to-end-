"""
Custom exception handler for DRF to return JSON instead of HTML for debug pages.
Ensures all 5xx errors return proper JSON error responses instead of debug HTML.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that:
    1. Converts debug HTML pages to JSON responses
    2. Ensures proper HTTP status codes
    3. Logs errors for debugging
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is None:
        # Unhandled exception - log it and return a generic error response
        logger.exception("Unhandled exception: %s", exc, exc_info=True)
        error_msg = str(exc.__class__.__name__) if getattr(settings, "DEBUG", False) else "Internal server error"
        return Response(
            {
                "detail": "Internal server error",
                "error": error_msg,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    # If response has been created, ensure it's JSON format
    if response.status_code >= 500:
        logger.error(
            f"5xx Error: {response.status_code}",
            extra={
                'status_code': response.status_code,
                'data': response.data if hasattr(response, 'data') else None
            }
        )
    
    return response
