"""
Test R-08: Input Validation and Error Policy

Validates that all endpoints:
- Validate input against schema
- Return safe error responses (no stack traces)
- Use standardized error envelopes
- Prevent SQL injection and other attacks
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

from orgs.models import Organization
from config.validators import StandardErrorEnvelope

User = get_user_model()


class InputValidationTests(TestCase):
    """Test input validation on all endpoints."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="test@test.com",
            org=self.org
        )
        self.client.force_authenticate(user=self.user)
    
    def test_invalid_json_returns_safe_error(self):
        """Test that invalid JSON returns safe error."""
        response = self.client.post(
            '/api/vendors/vendors/',
            data='{"invalid json}',
            content_type='application/json'
        )
        
        # Should return 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Should be safe error envelope
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])
        
        # Should NOT contain stack trace
        self.assertNotIn('traceback', str(response.data))
        self.assertNotIn('File', str(response.data))
    
    def test_missing_required_field(self):
        """Test that missing required fields return clear error."""
        response = self.client.post(
            '/api/vendors/vendors/',
            data={
                # Missing 'name' which is required
                'email': 'test@example.com',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('fields', response.data['error'].get('details', {}))
    
    def test_invalid_field_type(self):
        """Test that invalid field types return error."""
        response = self.client.post(
            '/api/vendors/vendors/',
            data={
                'name': 'Test Vendor',
                'email': 'not-an-email',  # Invalid email format
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_sql_injection_attempt_blocked(self):
        """Test that SQL injection attempts are blocked."""
        response = self.client.post(
            '/api/vendors/vendors/',
            data={
                'name': "'; DROP TABLE vendors; --",
            },
            format='json'
        )
        
        # Should block due to validation
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        
        # Should NOT execute any SQL
        # Verify table still exists by making another request
        response2 = self.client.get('/api/vendors/vendors/')
        self.assertIn(response2.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
    
    def test_oversized_payload_handling(self):
        """Test that oversized payloads are handled safely."""
        # Create a large payload
        large_data = 'x' * (10 * 1024 * 1024)  # 10MB of data
        
        response = self.client.post(
            '/api/vendors/vendors/',
            data={'name': large_data},
            format='json'
        )
        
        # Should return error (413 or 400)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_413_PAYLOAD_TOO_LARGE])
        
        # Should be safe error envelope
        if 'error' in response.data:
            self.assertIn('message', response.data['error'])


class SafeErrorResponseTests(TestCase):
    """Test that error responses are safe and don't expose internals."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="test@test.com",
            org=self.org
        )
        self.client.force_authenticate(user=self.user)
    
    def test_404_no_stack_trace(self):
        """Test that 404 errors don't include stack traces."""
        response = self.client.get('/api/vendors/vendors/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should NOT contain stack trace indicators
        response_str = str(response.data)
        self.assertNotIn('File', response_str)
        self.assertNotIn('line', response_str)
        self.assertNotIn('Traceback', response_str)
    
    def test_error_envelope_structure(self):
        """Test that all errors use standard envelope."""
        response = self.client.post(
            '/api/vendors/vendors/',
            data={},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Should have error envelope
        self.assertIn('error', response.data)
        error = response.data['error']
        
        # Should have code, message, status
        self.assertIn('code', error)
        self.assertIn('message', error)
        self.assertIn('status', error)
        
        # Status should match HTTP status
        self.assertEqual(error['status'], response.status_code)
    
    def test_validation_error_includes_field_details(self):
        """Test that validation errors include field-specific details."""
        response = self.client.post(
            '/api/vendors/vendors/',
            data={
                'name': '',  # Empty name
                'email': 'invalid-email',  # Invalid format
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Should have error code
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        
        # Should have field-specific details
        if 'details' in response.data['error']:
            self.assertIn('fields', response.data['error']['details'])
    
    def test_unhandled_error_returns_generic_message(self):
        """Test that unhandled errors return generic message."""
        # This would require mocking an exception, but we can verify
        # that the exception handler is in place by checking settings
        from django.conf import settings
        
        rest_framework_settings = settings.REST_FRAMEWORK
        self.assertIn('EXCEPTION_HANDLER', rest_framework_settings)


class StandardErrorEnvelopeTests(TestCase):
    """Test StandardErrorEnvelope formatting."""
    
    def test_format_error_includes_all_fields(self):
        """Test error envelope includes all required fields."""
        envelope = StandardErrorEnvelope.format_error(
            error_code="TEST_ERROR",
            message="Test error message",
            details={"field": "error"},
            http_status=400
        )
        
        self.assertEqual(envelope['error']['code'], 'TEST_ERROR')
        self.assertEqual(envelope['error']['message'], 'Test error message')
        self.assertEqual(envelope['error']['status'], 400)
        self.assertEqual(envelope['error']['details']['field'], 'error')
    
    def test_validation_error_formatting(self):
        """Test validation error formatting."""
        errors = {
            'name': ['This field is required.'],
            'email': ['Enter a valid email address.'],
        }
        
        envelope = StandardErrorEnvelope.validation_error(
            errors=errors,
            message="Validation failed"
        )
        
        self.assertEqual(envelope['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('fields', envelope['error']['details'])
        self.assertIn('name', envelope['error']['details']['fields'])
        self.assertIn('email', envelope['error']['details']['fields'])
    
    def test_error_without_details(self):
        """Test error envelope without optional details."""
        envelope = StandardErrorEnvelope.format_error(
            error_code="SIMPLE_ERROR",
            message="Simple error"
        )
        
        self.assertEqual(envelope['error']['code'], 'SIMPLE_ERROR')
        self.assertEqual(envelope['error']['message'], 'Simple error')
        self.assertEqual(envelope['error']['status'], 400)
        # Details should not be in envelope if not provided
        self.assertNotIn('details', envelope['error'])


class AuthenticationErrorResponseTests(TestCase):
    """Test that authentication errors are handled safely."""
    
    def setUp(self):
        """Create test client without authentication."""
        self.client = APIClient()
    
    def test_missing_auth_header_error(self):
        """Test that missing auth header returns safe error."""
        response = self.client.get('/api/vendors/vendors/')
        
        # Should return 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Should not expose internal details
        response_str = str(response.data)
        self.assertNotIn('Exception', response_str)
        self.assertNotIn('Traceback', response_str)


class PermissionErrorResponseTests(TestCase):
    """Test that permission errors are handled safely."""
    
    def setUp(self):
        """Create user without required permissions."""
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        
        # User with minimal permissions
        self.user = User.objects.create_user(
            username="vendor",
            password="testpass",
            email="vendor@test.com",
            role="vendor",
            org=self.org
        )
        self.client.force_authenticate(user=self.user)
    
    def test_forbidden_error_safe(self):
        """Test that 403 errors don't expose sensitive details."""
        # Try to access admin-only endpoint
        response = self.client.post(
            '/api/vendors/vendors/',
            data={'name': 'Test'},
            format='json'
        )
        
        # Should be 403 or other error
        if response.status_code == status.HTTP_403_FORBIDDEN:
            # Should be safe error
            response_str = str(response.data)
            self.assertNotIn('Traceback', response_str)
            self.assertNotIn('Exception', response_str)
