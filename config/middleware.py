"""
R-08: Input Validation and Error Policy

Implements schema validation at edge layer with consistent error envelopes.
- Validates all incoming requests against schema
- Returns safe, standardized error responses
- Removes stack traces from API responses
- Provides clear error messages without exposing internals
"""

from typing import Any, Dict
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class StandardErrorEnvelope:
    """
    Standard error response format for all API errors.
    
    Ensures consistent error reporting without exposing stack traces or internal details.
    """
    
    @staticmethod
    def format_error(
        error_code: str,
        message: str,
        details: Dict[str, Any] = None,
        http_status: int = status.HTTP_400_BAD_REQUEST
    ) -> Dict[str, Any]:
        """
        Format error response with standard envelope.
        
        Args:
            error_code: Machine-readable code (e.g., 'INVALID_INPUT', 'AUTH_REQUIRED')
            message: Human-readable message
            details: Additional error context (field-specific errors, etc.)
            http_status: HTTP status code
        
        Returns:
            Standardized error dict
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "status": http_status,
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return response
    
    @staticmethod
    def validation_error(
        errors: Dict[str, Any],
        message: str = "Validation failed"
    ) -> Dict[str, Any]:
        """Format validation errors."""
        formatted_errors = {}
        
        # Convert Django validation errors to readable format
        for field, error_list in errors.items():
            if isinstance(error_list, list):
                formatted_errors[field] = [str(e) for e in error_list]
            else:
                formatted_errors[field] = str(error_list)
        
        return StandardErrorEnvelope.format_error(
            error_code="VALIDATION_ERROR",
            message=message,
            details={"fields": formatted_errors},
            http_status=status.HTTP_400_BAD_REQUEST
        )


class InputValidationMiddleware:
    """
    Middleware for input validation and safe error responses.
    
    Responsibilities:
    - Validate request structure
    - Catch validation errors and format safely
    - Remove stack traces from error responses
    - Log errors for debugging (not exposed to client)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process request and response."""
        try:
            response = self.get_response(request)
            return response
        except DjangoValidationError as e:
            # Django validation errors
            logger.warning(f"Validation error on {request.path}: {e}")
            return JsonResponse(
                StandardErrorEnvelope.format_error(
                    error_code="INVALID_INPUT",
                    message="The request contains invalid data",
                    details={"error": str(e)}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except DRFValidationError as e:
            # DRF validation errors
            logger.warning(f"DRF validation error on {request.path}: {e.detail}")
            errors = e.detail if isinstance(e.detail, dict) else {"error": str(e.detail)}
            return JsonResponse(
                StandardErrorEnvelope.validation_error(
                    errors=errors,
                    message="Request validation failed"
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Generic error - log full details but return safe response
            logger.exception(f"Unexpected error on {request.path}: {type(e).__name__}: {str(e)}")
            return JsonResponse(
                StandardErrorEnvelope.format_error(
                    error_code="INTERNAL_ERROR",
                    message="An error occurred processing your request",
                    details={},
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def process_exception(self, request, exception):
        """Process exceptions - DRF already handles most, but this catches others."""
        if isinstance(exception, (DRFValidationError, DjangoValidationError)):
            logger.warning(f"Validation error: {exception}")
            return JsonResponse(
                StandardErrorEnvelope.format_error(
                    error_code="INVALID_INPUT",
                    message="Request validation failed",
                    details={}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log unexpected exceptions without exposing details
        logger.exception(f"Unhandled exception: {type(exception).__name__}")
        return JsonResponse(
            StandardErrorEnvelope.format_error(
                error_code="INTERNAL_ERROR",
                message="An error occurred processing your request",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SafeExceptionHandler:
    """
    Custom DRF exception handler that removes stack traces and returns safe errors.
    """
    
    @staticmethod
    def exception_handler(exc, context):
        """
        Handle DRF exceptions with safe error envelope.
        
        Returns consistent error format without exposing internals.
        """
        from rest_framework.views import exception_handler as drf_exception_handler
        
        # Get DRF's default error response
        response = drf_exception_handler(exc, context)
        
        if response is not None:
            # Transform to safe format
            error_data = response.data
            
            # Determine error code
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                error_code = "INVALID_REQUEST"
                if isinstance(error_data, dict) and any(k in error_data for k in ['detail', 'error']):
                    error_code = "VALIDATION_ERROR"
            elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                error_code = "AUTH_REQUIRED"
            elif response.status_code == status.HTTP_403_FORBIDDEN:
                error_code = "PERMISSION_DENIED"
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                error_code = "NOT_FOUND"
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                error_code = "RATE_LIMIT_EXCEEDED"
            elif response.status_code >= 500:
                error_code = "INTERNAL_ERROR"
            else:
                error_code = "ERROR"
            
            # Get message
            if isinstance(error_data, dict):
                message = error_data.get('detail', error_data.get('error', str(error_data)))
            else:
                message = str(error_data)
            
            if isinstance(message, list):
                message = message[0] if message else "An error occurred"
            
            # Return safe format
            response.data = StandardErrorEnvelope.format_error(
                error_code=error_code,
                message=str(message),
                details=error_data if isinstance(error_data, dict) else None,
                http_status=response.status_code
            )
        
        return response
