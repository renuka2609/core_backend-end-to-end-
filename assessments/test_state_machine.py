"""
Test Assessment State Transitions (R-06)

Tests for strict state machine with 409 conflict responses on invalid transitions.
"""

import json
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from assessments.models import Assessment
from assessments.services import AssessmentStateTransitionService, StateTransitionError
from vendors.models import Vendor
from templates.models import Template, TemplateVersion
from orgs.models import Organization
from permissions.constants import Roles
from audit.models import AuditEvent

User = get_user_model()


class AssessmentStateTransitionTests(TestCase):
    """Test Assessment state machine."""
    
    def setUp(self):
        """Create test data."""
        self.org = Organization.objects.create(name="Test Org")
        self.vendor = Vendor.objects.create(name="Test Vendor", org=self.org)
        self.template = Template.objects.create(
            name="Test Template",
            org=self.org,
            description="Test"
        )
        
        self.admin_user = User.objects.create_user(
            username="admin_user",
            password="testpass",
            email="admin@test.com",
            role=Roles.ADMIN,
            org=self.org
        )
        
        self.vendor_user = User.objects.create_user(
            username="vendor_user",
            password="testpass",
            email="vendor@test.com",
            role=Roles.VENDOR,
            org=self.org
        )
        
        self.reviewer_user = User.objects.create_user(
            username="reviewer_user",
            password="testpass",
            email="reviewer@test.com",
            role=Roles.REVIEWER,
            org=self.org
        )
        
        self.assessment = Assessment.objects.create(
            org=self.org,
            vendor=self.vendor,
            template=self.template,
            status=Assessment.STATUS_ASSIGNED
        )
    
    def test_valid_transition_assigned_to_submitted(self):
        """Test valid transition: assigned → submitted"""
        result = AssessmentStateTransitionService.transition(
            assessment=self.assessment,
            new_status=Assessment.STATUS_SUBMITTED,
            actor_user=self.vendor_user
        )
        
        self.assertEqual(result.status, Assessment.STATUS_SUBMITTED)
        # Verify audit event was created
        audit_events = AuditEvent.objects.filter(
            resource_id=self.assessment.id,
            resource_type="assessment"
        )
        self.assertEqual(audit_events.count(), 1)
        self.assertIn("assigned → submitted", audit_events.first().action)
    
    def test_valid_transition_chain(self):
        """Test full valid transition chain."""
        # assigned → submitted
        result = AssessmentStateTransitionService.transition(
            self.assessment, Assessment.STATUS_SUBMITTED, self.vendor_user
        )
        self.assertEqual(result.status, Assessment.STATUS_SUBMITTED)
        
        # submitted → reviewed
        result = AssessmentStateTransitionService.transition(
            result, Assessment.STATUS_REVIEWED, self.reviewer_user
        )
        self.assertEqual(result.status, Assessment.STATUS_REVIEWED)
        
        # reviewed → approved
        result = AssessmentStateTransitionService.transition(
            result, Assessment.STATUS_APPROVED, self.admin_user
        )
        self.assertEqual(result.status, Assessment.STATUS_APPROVED)
        
        # Should have 3 audit events
        audit_events = AuditEvent.objects.filter(
            resource_id=self.assessment.id,
            resource_type="assessment"
        ).order_by('created_at')
        self.assertEqual(audit_events.count(), 3)
    
    def test_invalid_transition_assigned_to_reviewed(self):
        """Test invalid transition: assigned → reviewed (should fail)"""
        with self.assertRaises(StateTransitionError) as ctx:
            AssessmentStateTransitionService.transition(
                self.assessment,
                Assessment.STATUS_REVIEWED,
                self.reviewer_user
            )
        
        self.assertIn("Cannot transition", str(ctx.exception))
        self.assertEqual(self.assessment.status, Assessment.STATUS_ASSIGNED)
    
    def test_invalid_transition_assigned_to_approved(self):
        """Test invalid transition: assigned → approved (should fail)"""
        with self.assertRaises(StateTransitionError):
            AssessmentStateTransitionService.transition(
                self.assessment,
                Assessment.STATUS_APPROVED,
                self.admin_user
            )
    
    def test_no_transition_from_approved(self):
        """Test that approved state has no valid transitions."""
        # Move to approved
        self.assessment.status = Assessment.STATUS_APPROVED
        self.assessment.save()
        
        # Try any transition
        with self.assertRaises(StateTransitionError):
            AssessmentStateTransitionService.transition(
                self.assessment,
                Assessment.STATUS_REMEDIATION,
                self.reviewer_user
            )
    
    def test_remediation_transition(self):
        """Test transition to remediation and back to reviewed."""
        # Get to reviewed state first
        self.assessment.status = Assessment.STATUS_REVIEWED
        self.assessment.save()
        
        # reviewed → remediation
        result = AssessmentStateTransitionService.transition(
            self.assessment,
            Assessment.STATUS_REMEDIATION,
            self.reviewer_user
        )
        self.assertEqual(result.status, Assessment.STATUS_REMEDIATION)
        
        # remediation → reviewed (vendor resubmits)
        result = AssessmentStateTransitionService.transition(
            result,
            Assessment.STATUS_REVIEWED,
            self.reviewer_user
        )
        self.assertEqual(result.status, Assessment.STATUS_REVIEWED)
    
    def test_get_valid_next_states(self):
        """Test getting valid next states."""
        self.assessment.status = Assessment.STATUS_SUBMITTED
        
        valid_states = AssessmentStateTransitionService.get_valid_next_states(self.assessment)
        self.assertEqual(valid_states, [Assessment.STATUS_REVIEWED])
    
    def test_audit_event_metadata(self):
        """Test audit event contains proper metadata."""
        AssessmentStateTransitionService.transition(
            self.assessment,
            Assessment.STATUS_SUBMITTED,
            self.vendor_user,
            metadata={"reason": "vendor_ready"}
        )
        
        audit_event = AuditEvent.objects.filter(
            resource_id=self.assessment.id
        ).first()
        
        self.assertIsNotNone(audit_event)
        self.assertEqual(audit_event.user, self.vendor_user)
        self.assertEqual(audit_event.resource_type, "assessment")
        self.assertEqual(audit_event.resource_id, self.assessment.id)
        
        metadata = json.loads(audit_event.metadata)
        self.assertEqual(metadata["old_value"], Assessment.STATUS_ASSIGNED)
        self.assertEqual(metadata["new_value"], Assessment.STATUS_SUBMITTED)
        self.assertEqual(metadata["reason"], "vendor_ready")


class AssessmentViewTransitionTests(TestCase):
    """Test Assessment API endpoints for state transitions with 409 conflicts."""
    
    def setUp(self):
        """Create test data and API client."""
        self.client = APIClient()
        
        self.org = Organization.objects.create(name="Test Org")
        self.vendor = Vendor.objects.create(name="Test Vendor", org=self.org)
        self.template = Template.objects.create(
            name="Test Template",
            org=self.org,
            description="Test"
        )
        
        self.vendor_user = User.objects.create_user(
            username="vendor",
            password="testpass",
            email="vendor@test.com",
            role=Roles.VENDOR,
            org=self.org
        )
        
        self.reviewer_user = User.objects.create_user(
            username="reviewer",
            password="testpass",
            email="reviewer@test.com",
            role=Roles.REVIEWER,
            org=self.org
        )
        
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass",
            email="admin@test.com",
            role=Roles.ADMIN,
            org=self.org
        )
        
        self.assessment = Assessment.objects.create(
            org=self.org,
            vendor=self.vendor,
            template=self.template,
            status=Assessment.STATUS_ASSIGNED
        )
    
    def test_submit_endpoint_success(self):
        """Test /submit endpoint with valid transition."""
        self.client.force_authenticate(user=self.vendor_user)
        
        response = self.client.post(
            f'/api/assessments/assessments/{self.assessment.id}/submit/',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.status, Assessment.STATUS_SUBMITTED)
    
    def test_submit_endpoint_409_conflict(self):
        """Test /submit endpoint returns 409 for invalid transition."""
        # Move to submitted first
        self.assessment.status = Assessment.STATUS_SUBMITTED
        self.assessment.save()
        
        self.client.force_authenticate(user=self.vendor_user)
        
        # Try to submit again (invalid transition)
        response = self.client.post(
            f'/api/assessments/assessments/{self.assessment.id}/submit/',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Cannot transition", response.data["error"])
        self.assertIn("valid_transitions", response.data)
    
    def test_review_endpoint_success(self):
        """Test /review endpoint with valid transition."""
        self.assessment.status = Assessment.STATUS_SUBMITTED
        self.assessment.save()
        
        self.client.force_authenticate(user=self.reviewer_user)
        
        response = self.client.post(
            f'/api/assessments/assessments/{self.assessment.id}/review/',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.status, Assessment.STATUS_REVIEWED)
    
    def test_review_endpoint_409_conflict(self):
        """Test /review endpoint returns 409 for invalid transition."""
        # Assessment is in ASSIGNED state
        self.client.force_authenticate(user=self.reviewer_user)
        
        response = self.client.post(
            f'/api/assessments/assessments/{self.assessment.id}/review/',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Cannot transition", response.data["error"])
    
    def test_approve_endpoint_success(self):
        """Test /approve endpoint with valid transition."""
        self.assessment.status = Assessment.STATUS_REVIEWED
        self.assessment.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/assessments/assessments/{self.assessment.id}/approve/',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.status, Assessment.STATUS_APPROVED)
        self.assertIsNotNone(self.assessment.score)
        self.assertIsNotNone(self.assessment.risk_level)
    
    def test_approve_endpoint_409_conflict(self):
        """Test /approve endpoint returns 409 for invalid transition."""
        # Assessment is in ASSIGNED state
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/assessments/assessments/{self.assessment.id}/approve/',
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Cannot transition", response.data["error"])
