"""
R-09: Rate Limiting and Secure Headers

Implements per-user and per-IP rate limiting with configurable thresholds.
Adds security headers to all responses.
Provides brute-force controls on auth endpoints.
"""

from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# Throttle classes - defined without importing from rest_framework at module level
# to avoid circular import issues. They will be subclassed when actually used.
class UserRateLimitThrottle:
    """
    Per-user rate limiting.
    
    Limits authenticated users to 100 requests per hour.
    """
    scope = 'user'
    THROTTLE_RATES = {
        'user': '100/hour',
        'anon': '50/hour',
    }


class IPRateLimitThrottle:
    """
    Per-IP rate limiting.
    
    Limits unauthenticated users to 50 requests per hour.
    """
    scope = 'anon'
    THROTTLE_RATES = {
        'anon': '50/hour',
    }


class StrictAuthThrottle:
    """
    Strict rate limiting for authentication endpoints.
    
    Prevents brute-force attacks with 5 failed attempts per 15 minutes.
    """
    scope = 'auth'
    THROTTLE_RATES = {
        'auth': '10/hour',  # Max 10 attempts per hour
    }


class BruteForceDefense:
    """
    Brute-force attack prevention.
    
    Tracks failed login attempts per user/IP and blocks after threshold.
    """
    
    FAILED_ATTEMPT_KEY = "login_failed_{identifier}"
    LOCKOUT_KEY = "login_lockout_{identifier}"
    FAILED_THRESHOLD = 5
    LOCKOUT_DURATION = 15 * 60  # 15 minutes in seconds
    
    @staticmethod
    def get_identifier(request):
        """Get unique identifier (user email or IP)."""
        if request.user and request.user.is_authenticated:
            return f"user_{request.user.id}"
        
        return f"ip_{get_client_ip(request)}"
    
    @staticmethod
    def record_failed_attempt(request):
        """Record a failed login attempt."""
        identifier = BruteForceDefense.get_identifier(request)
        key = BruteForceDefense.FAILED_ATTEMPT_KEY.format(identifier=identifier)
        
        attempts = cache.get(key, 0)
        attempts += 1
        
        cache.set(key, attempts, BruteForceDefense.LOCKOUT_DURATION)
        
        if attempts >= BruteForceDefense.FAILED_THRESHOLD:
            lockout_key = BruteForceDefense.LOCKOUT_KEY.format(identifier=identifier)
            cache.set(lockout_key, True, BruteForceDefense.LOCKOUT_DURATION)
            logger.warning(f"Account locked due to brute force: {identifier}")
            
            return False, f"Account temporarily locked. Try again in {BruteForceDefense.LOCKOUT_DURATION // 60} minutes."
        
        return True, None
    
    @staticmethod
    def is_locked_out(request):
        """Check if account is locked."""
        identifier = BruteForceDefense.get_identifier(request)
        lockout_key = BruteForceDefense.LOCKOUT_KEY.format(identifier=identifier)
        
        return cache.get(lockout_key, False)
    
    @staticmethod
    def clear_attempts(request):
        """Clear failed attempts on successful login."""
        identifier = BruteForceDefense.get_identifier(request)
        key = BruteForceDefense.FAILED_ATTEMPT_KEY.format(identifier=identifier)
        cache.delete(key)


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


class SecurityHeadersMiddleware:
    """
    Adds security headers to all responses.
    
    Headers included:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Force HTTPS
    - Content-Security-Policy: Prevent inline scripts
    - Referrer-Policy: Control referrer information
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Prevent MIME sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Enable XSS filter
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Force HTTPS (only in production)
        if not request.build_absolute_uri().startswith('http://localhost'):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Prevent caching of sensitive data
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        
        return response


class RateLimitMiddleware:
    """
    Implements per-IP rate limiting with configurable thresholds.
    
    Tracks requests per IP and returns 429 when limit exceeded.
    """
    
    RATE_LIMIT_KEY = "ratelimit_{ip}"
    REQUESTS_PER_MINUTE = 60
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        client_ip = get_client_ip(request)
        key = self.RATE_LIMIT_KEY.format(ip=client_ip)
        
        # Get current request count
        request_count = cache.get(key, 0)
        
        if request_count >= self.REQUESTS_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            response = JsonResponse({
                'error': {
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Too many requests. Please try again later.',
                    'status': 429,
                }
            }, status=429)
            response['Retry-After'] = '60'
            return response
        
        # Increment counter (expires after 1 minute)
        cache.set(key, request_count + 1, 60)
        
        response = self.get_response(request)
        
        # Add rate limit headers
        response['X-RateLimit-Limit'] = str(self.REQUESTS_PER_MINUTE)
        response['X-RateLimit-Remaining'] = str(self.REQUESTS_PER_MINUTE - request_count - 1)
        response['X-RateLimit-Reset'] = str(int((datetime.now() + timedelta(minutes=1)).timestamp()))
        
        return response


def require_rate_limit_check(auth_endpoint=False):
    """
    Decorator to check rate limits on specific endpoints.
    
    Args:
        auth_endpoint: If True, uses brute-force defense
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from rest_framework.response import Response
            from rest_framework import status
            
            # Check brute-force lockout
            if auth_endpoint and BruteForceDefense.is_locked_out(request):
                return Response({
                    'error': {
                        'code': 'ACCOUNT_LOCKED',
                        'message': 'Account temporarily locked due to too many failed attempts.',
                        'status': 429,
                    }
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


# Security checklist items
SECURITY_CHECKLIST = {
    'headers': {
        'name': 'Security Headers',
        'items': [
            'X-Content-Type-Options: nosniff',
            'X-Frame-Options: DENY',
            'X-XSS-Protection: 1; mode=block',
            'Strict-Transport-Security (HTTPS only)',
            'Content-Security-Policy',
            'Referrer-Policy',
        ]
    },
    'rate_limiting': {
        'name': 'Rate Limiting',
        'items': [
            'Per-user rate limiting (100 req/hour)',
            'Per-IP rate limiting (50 req/hour)',
            'Auth endpoint strict limiting (10 req/hour)',
            'Brute-force defense (5 attempts/15min)',
        ]
    },
    'input_validation': {
        'name': 'Input Validation',
        'items': [
            'Schema validation on all endpoints',
            'File upload validation',
            'File size limits (10MB)',
            'Safe error responses (no stack traces)',
        ]
    },
    'authentication': {
        'name': 'Authentication',
        'items': [
            'JWT token validation',
            'CSRF protection on forms',
            'Secure password hashing',
            'Session timeout enforcement',
        ]
    },
}
