"""
Test Immutable Audit Ledger (R-07)

Tests for append-only audit event API with resource tracking, filtering, and search.
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from audit.models import AuditEvent
from orgs.models import Organization

User = get_user_model()


class AuditEventAPITests(TestCase):
    """Test Audit Event API endpoints."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name="Test Org")
        
        self.user1 = User.objects.create_user(
            username="user1",
            password="testpass",
            email="user1@test.com",
            org=self.org
        )
        
        self.user2 = User.objects.create_user(
            username="user2",
            password="testpass",
            email="user2@test.com",
            org=self.org
        )
        
        # Create audit events
        self.event1 = AuditEvent.objects.create(
            user=self.user1,
            org=self.org,
            action="assessment_created",
            resource_type="assessment",
            resource_id=1,
            metadata={
                "resource": "assessment",
                "resource_id": 1,
                "action": "create",
                "vendor_id": 5,
            }
        )
        
        self.event2 = AuditEvent.objects.create(
            user=self.user1,
            org=self.org,
            action="assessment_transitioned: assigned → submitted",
            resource_type="assessment",
            resource_id=1,
            metadata={
                "resource": "assessment",
                "resource_id": 1,
                "action": "state_transition",
                "old_value": "assigned",
                "new_value": "submitted",
            }
        )
        
        self.event3 = AuditEvent.objects.create(
            user=self.user2,
            org=self.org,
            action="assessment_transitioned: submitted → reviewed",
            resource_type="assessment",
            resource_id=1,
            metadata={
                "resource": "assessment",
                "resource_id": 1,
                "action": "state_transition",
                "old_value": "submitted",
                "new_value": "reviewed",
            }
        )
    
    def test_list_audit_events(self):
        """Test listing audit events."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 3)
    
    def test_filter_by_resource_type(self):
        """Test filtering audit events by resource type."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/?resource_type=assessment')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for event in response.data['results']:
            self.assertEqual(event['resource_type'], 'assessment')
    
    def test_filter_by_resource_id(self):
        """Test filtering audit events by resource ID."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/?resource_id=1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for event in response.data['results']:
            self.assertEqual(event['resource_id'], 1)
    
    def test_filter_by_user(self):
        """Test filtering audit events by user."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(f'/api/audit/events/?user={self.user1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for event in response.data['results']:
            self.assertEqual(event['user'], self.user1.id)
    
    def test_search_in_action(self):
        """Test searching in action field."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/?search=transitioned')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find events with "transitioned" in action
        self.assertGreaterEqual(len(response.data['results']), 2)
    
    def test_search_by_username(self):
        """Test searching by username."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/?search=user2')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find events from user2
        found_user2_event = any(
            e['user'] == self.user2.id for e in response.data['results']
        )
        self.assertTrue(found_user2_event)
    
    def test_ordering_by_created_at_desc(self):
        """Test ordering by created_at descending (default)."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/?ordering=-created_at')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        if len(results) > 1:
            # Newer events should come first
            self.assertGreaterEqual(
                results[0]['created_at'],
                results[-1]['created_at']
            )
    
    def test_by_resource_endpoint(self):
        """Test /by_resource endpoint for complete resource audit trail."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(
            '/api/audit/events/by_resource/?resource_type=assessment&resource_id=1'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['resource_type'], 'assessment')
        self.assertEqual(response.data['resource_id'], 1)
        self.assertEqual(response.data['event_count'], 3)
        # Should have all audit trail in chronological order
        audit_trail = response.data['audit_trail']
        self.assertEqual(len(audit_trail), 3)
    
    def test_by_resource_endpoint_missing_params(self):
        """Test /by_resource endpoint returns 400 with missing params."""
        self.client.force_authenticate(user=self.user1)
        
        # Missing resource_id
        response = self.client.get(
            '/api/audit/events/by_resource/?resource_type=assessment'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_by_resource_endpoint_invalid_resource_id(self):
        """Test /by_resource endpoint with invalid resource_id."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(
            '/api/audit/events/by_resource/?resource_type=assessment&resource_id=abc'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('integer', response.data['error'])
    
    def test_by_user_endpoint(self):
        """Test /by_user endpoint for user action audit trail."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(f'/api/audit/events/by_user/?user_id={self.user1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user1.id)
        # Should have 2 events from user1
        self.assertEqual(response.data['action_count'], 2)
    
    def test_by_user_endpoint_missing_param(self):
        """Test /by_user endpoint returns 400 with missing param."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/by_user/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_by_date_range_endpoint(self):
        """Test /by_date_range endpoint for time-window audit."""
        self.client.force_authenticate(user=self.user1)
        
        now = datetime.utcnow()
        start = (now - timedelta(hours=1)).isoformat() + 'Z'
        end = (now + timedelta(hours=1)).isoformat() + 'Z'
        
        response = self.client.get(
            f'/api/audit/events/by_date_range/?start_date={start}&end_date={end}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['event_count'], 3)
    
    def test_by_date_range_endpoint_missing_params(self):
        """Test /by_date_range endpoint returns 400 with missing params."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get('/api/audit/events/by_date_range/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_by_date_range_endpoint_invalid_format(self):
        """Test /by_date_range endpoint with invalid date format."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(
            '/api/audit/events/by_date_range/?start_date=2026-01-01&end_date=invalid'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ISO 8601', response.data['error'])
    
    def test_immutability_create_blocked(self):
        """Test that creating audit events via API is blocked."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post(
            '/api/audit/events/',
            {
                'action': 'test_action',
                'resource_type': 'test',
                'resource_id': 1,
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('immutable', response.data['error'].lower())
    
    def test_immutability_update_blocked(self):
        """Test that updating audit events via API is blocked."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.patch(
            f'/api/audit/events/{self.event1.id}/',
            {'action': 'modified_action'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('not allowed', response.data['detail'].lower())
    
    def test_immutability_delete_blocked(self):
        """Test that deleting audit events via API is blocked."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.delete(f'/api/audit/events/{self.event1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertIn('immutable', response.data['error'].lower())
    
    def test_audit_event_metadata_structure(self):
        """Test that audit events contain proper metadata."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(f'/api/audit/events/{self.event2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event = response.data
        
        # Check structure
        self.assertIn('user', event)
        self.assertIn('user_details', event)
        self.assertIn('action', event)
        self.assertIn('resource_type', event)
        self.assertIn('resource_id', event)
        self.assertIn('metadata', event)
        self.assertIn('created_at', event)
        
        # Check user details
        self.assertEqual(event['user'], self.user1.id)
        self.assertEqual(event['user_details']['username'], 'user1')
        self.assertEqual(event['user_details']['email'], 'user1@test.com')
        
        # Check metadata
        metadata = event['metadata']
        self.assertEqual(metadata['old_value'], 'assigned')
        self.assertEqual(metadata['new_value'], 'submitted')
