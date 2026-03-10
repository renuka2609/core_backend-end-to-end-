#!/usr/bin/env python
"""
Integration tests for cross-tenant access denial.

These tests verify that the tenant-aware query guards properly prevent
users from accessing data belonging to other organizations/tenants.
"""
import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from assessments.models import Assessment
from reviews.models import Review
from evidence.models import Evidence
from responses.models import Response
from remediations.models import Remediation
from vendors.models import Vendor
from templates.models import Template
from orgs.models import Organization


class TestCrossTenantAccessDenial:
    """Test suite for cross-tenant access denial."""
    
    def __init__(self):
        self.client = APIClient()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_test(self, test_name, status_code, expected_status, passed, details=""):
        """Log test results."""
        status_text = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status_text} | {test_name}")
        print(f"   Status: {status_code} (expected {expected_status})")
        if details:
            print(f"   Details: {details}")
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append({
                'test': test_name,
                'status_code': status_code,
                'expected': expected_status,
                'details': details
            })
    
    def setup_test_data(self):
        """Create test organizations and users."""
        # Create two organizations
        self.org1 = Organization.objects.create(name="Organization 1", code="ORG1")
        self.org2 = Organization.objects.create(name="Organization 2", code="ORG2")
        
        # Create users in different organizations
        self.user_org1_admin = User.objects.create_user(
            username="admin_org1",
            password="testpass123",
            org=self.org1,
            role="admin"
        )
        
        self.user_org2_admin = User.objects.create_user(
            username="admin_org2",
            password="testpass123",
            org=self.org2,
            role="admin"
        )
        
        self.user_org1_reviewer = User.objects.create_user(
            username="reviewer_org1",
            password="testpass123",
            org=self.org1,
            role="reviewer"
        )
        
        # Create test data for org1
        self.assessment_org1 = Assessment.objects.create(
            org=self.org1,
            name="Assessment Org1",
            status="draft"
        )
        
        self.review_org1 = Review.objects.create(
            org=self.org1,
            assessment=self.assessment_org1,
            reviewer=self.user_org1_reviewer
        )
        
        self.template_org1 = Template.objects.create(
            org=self.org1,
            name="Template Org1"
        )
        
        self.vendor_org1 = Vendor.objects.create(
            org=self.org1,
            name="Vendor Org1",
            email="vendor1@org1.com"
        )
        
        # Create test data for org2
        self.assessment_org2 = Assessment.objects.create(
            org=self.org2,
            name="Assessment Org2",
            status="draft"
        )
        
        self.review_org2 = Review.objects.create(
            org=self.org2,
            assessment=self.assessment_org2,
            reviewer=self.user_org2_admin
        )
        
        self.template_org2 = Template.objects.create(
            org=self.org2,
            name="Template Org2"
        )
        
        self.vendor_org2 = Vendor.objects.create(
            org=self.org2,
            name="Vendor Org2",
            email="vendor2@org2.com"
        )
        
        # Create evidence for org1
        self.evidence_org1 = Evidence.objects.create(
            assessment=self.assessment_org1,
            uploaded_by=self.user_org1_admin,
            description="Evidence Org1"
        )
        
        # Create response for org1
        self.response_org1 = Response.objects.create(
            assessment=self.assessment_org1,
            answer="Response Org1"
        )
        
        print("\n" + "=" * 80)
        print("TEST DATA SETUP COMPLETE")
        print(f"Org1 ID: {self.org1.id}, Org2 ID: {self.org2.id}")
        print(f"Assessment Org1 ID: {self.assessment_org1.id}")
        print(f"Assessment Org2 ID: {self.assessment_org2.id}")
        print("=" * 80)
    
    def test_assessment_list_isolation(self):
        """Test: Assessment list endpoint only shows user's org assessments."""
        print("\n" + "-" * 80)
        print("TEST: Assessment List Isolation")
        print("-" * 80)
        
        # User from org1 should only see org1 assessments
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get('/api/assessments/')
        
        passed = (resp.status_code == status.HTTP_200_OK and 
                 len(resp.data) == 1 and 
                 resp.data[0]['id'] == self.assessment_org1.id)
        
        self.log_test(
            "Org1 user sees only Org1 assessments in list",
            resp.status_code,
            status.HTTP_200_OK,
            passed,
            f"Results: {[a['id'] for a in resp.data]}"
        )
    
    def test_assessment_detail_cross_tenant_deny(self):
        """Test: Cannot access detail of another tenant's assessment."""
        print("\n" + "-" * 80)
        print("TEST: Assessment Detail Cross-Tenant Access Denial")
        print("-" * 80)
        
        # User from org1 should NOT access org2 assessment detail
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get(f'/api/assessments/{self.assessment_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot access Org2 assessment detail",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_review_list_isolation(self):
        """Test: Review list endpoint only shows user's org reviews."""
        print("\n" + "-" * 80)
        print("TEST: Review List Isolation")
        print("-" * 80)
        
        # User from org1 should only see org1 reviews
        self.client.force_authenticate(user=self.user_org1_reviewer)
        resp = self.client.get('/api/reviews/')
        
        passed = (resp.status_code == status.HTTP_200_OK and 
                 len(resp.data) == 1 and 
                 resp.data[0]['id'] == self.review_org1.id)
        
        self.log_test(
            "Org1 reviewer sees only Org1 reviews in list",
            resp.status_code,
            status.HTTP_200_OK,
            passed,
            f"Results: {[r['id'] for r in resp.data]}"
        )
    
    def test_review_detail_cross_tenant_deny(self):
        """Test: Cannot access detail of another tenant's review."""
        print("\n" + "-" * 80)
        print("TEST: Review Detail Cross-Tenant Access Denial")
        print("-" * 80)
        
        # User from org1 should NOT access org2 review detail
        self.client.force_authenticate(user=self.user_org1_reviewer)
        resp = self.client.get(f'/api/reviews/{self.review_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 reviewer cannot access Org2 review detail",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_template_list_isolation(self):
        """Test: Template list endpoint only shows user's org templates."""
        print("\n" + "-" * 80)
        print("TEST: Template List Isolation")
        print("-" * 80)
        
        # User from org1 should only see org1 templates
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get('/api/templates/')
        
        passed = (resp.status_code == status.HTTP_200_OK and 
                 len(resp.data) == 1 and 
                 resp.data[0]['id'] == self.template_org1.id)
        
        self.log_test(
            "Org1 user sees only Org1 templates in list",
            resp.status_code,
            status.HTTP_200_OK,
            passed,
            f"Results: {[t['id'] for t in resp.data]}"
        )
    
    def test_template_detail_cross_tenant_deny(self):
        """Test: Cannot access detail of another tenant's template."""
        print("\n" + "-" * 80)
        print("TEST: Template Detail Cross-Tenant Access Denial")
        print("-" * 80)
        
        # User from org1 should NOT access org2 template detail
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get(f'/api/templates/{self.template_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot access Org2 template detail",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_vendor_list_isolation(self):
        """Test: Vendor list endpoint only shows user's org vendors."""
        print("\n" + "-" * 80)
        print("TEST: Vendor List Isolation")
        print("-" * 80)
        
        # User from org1 should only see org1 vendors
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get('/api/vendors/')
        
        passed = (resp.status_code == status.HTTP_200_OK and 
                 len(resp.data) == 1 and 
                 resp.data[0]['id'] == self.vendor_org1.id)
        
        self.log_test(
            "Org1 user sees only Org1 vendors in list",
            resp.status_code,
            status.HTTP_200_OK,
            passed,
            f"Results: {[v['id'] for v in resp.data]}"
        )
    
    def test_vendor_detail_cross_tenant_deny(self):
        """Test: Cannot access detail of another tenant's vendor."""
        print("\n" + "-" * 80)
        print("TEST: Vendor Detail Cross-Tenant Access Denial")
        print("-" * 80)
        
        # User from org1 should NOT access org2 vendor detail
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get(f'/api/vendors/{self.vendor_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot access Org2 vendor detail",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_evidence_list_isolation(self):
        """Test: Evidence list endpoint only shows user's org evidence."""
        print("\n" + "-" * 80)
        print("TEST: Evidence List Isolation")
        print("-" * 80)
        
        # User from org1 should only see org1 evidence
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get('/api/evidence/')
        
        passed = (resp.status_code == status.HTTP_200_OK and 
                 len(resp.data) == 1 and 
                 resp.data[0]['id'] == self.evidence_org1.id)
        
        self.log_test(
            "Org1 user sees only Org1 evidence in list",
            resp.status_code,
            status.HTTP_200_OK,
            passed,
            f"Results: {[e['id'] for e in resp.data]}"
        )
    
    def test_evidence_detail_cross_tenant_deny(self):
        """Test: Cannot access detail of another tenant's evidence."""
        print("\n" + "-" * 80)
        print("TEST: Evidence Detail Cross-Tenant Access Denial")
        print("-" * 80)
        
        # Create evidence for org2 first
        evidence_org2 = Evidence.objects.create(
            assessment=self.assessment_org2,
            uploaded_by=self.user_org2_admin,
            description="Evidence Org2"
        )
        
        # User from org1 should NOT access org2 evidence detail
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get(f'/api/evidence/{evidence_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot access Org2 evidence detail",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_response_list_isolation(self):
        """Test: Response list endpoint only shows user's org responses."""
        print("\n" + "-" * 80)
        print("TEST: Response List Isolation")
        print("-" * 80)
        
        # User from org1 should only see org1 responses
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get('/api/responses/')
        
        passed = (resp.status_code == status.HTTP_200_OK and 
                 len(resp.data) == 1 and 
                 resp.data[0]['id'] == self.response_org1.id)
        
        self.log_test(
            "Org1 user sees only Org1 responses in list",
            resp.status_code,
            status.HTTP_200_OK,
            passed,
            f"Results: {[r['id'] for r in resp.data]}"
        )
    
    def test_response_detail_cross_tenant_deny(self):
        """Test: Cannot access detail of another tenant's response."""
        print("\n" + "-" * 80)
        print("TEST: Response Detail Cross-Tenant Access Denial")
        print("-" * 80)
        
        # Create response for org2 first
        response_org2 = Response.objects.create(
            assessment=self.assessment_org2,
            answer="Response Org2"
        )
        
        # User from org1 should NOT access org2 response detail
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.get(f'/api/responses/{response_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot access Org2 response detail",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_cross_tenant_update_denied(self):
        """Test: Cannot update another tenant's resources."""
        print("\n" + "-" * 80)
        print("TEST: Cross-Tenant Update Denial")
        print("-" * 80)
        
        # User from org1 should NOT be able to update org2 assessment
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.patch(
            f'/api/assessments/{self.assessment_org2.id}/',
            {'status': 'approved'},
            format='json'
        )
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot update Org2 assessment",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_cross_tenant_delete_denied(self):
        """Test: Cannot delete another tenant's resources."""
        print("\n" + "-" * 80)
        print("TEST: Cross-Tenant Delete Denial")
        print("-" * 80)
        
        # User from org1 should NOT be able to delete org2 template
        self.client.force_authenticate(user=self.user_org1_admin)
        resp = self.client.delete(f'/api/templates/{self.template_org2.id}/')
        
        passed = resp.status_code == status.HTTP_403_FORBIDDEN
        
        self.log_test(
            "Org1 user cannot delete Org2 template",
            resp.status_code,
            status.HTTP_403_FORBIDDEN,
            passed
        )
    
    def test_unauthenticated_access_denied(self):
        """Test: Unauthenticated requests are denied."""
        print("\n" + "-" * 80)
        print("TEST: Unauthenticated Access Denial")
        print("-" * 80)
        
        # Clear authentication
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/assessments/')
        
        passed = resp.status_code == status.HTTP_401_UNAUTHORIZED
        
        self.log_test(
            "Unauthenticated user denied access to assessments",
            resp.status_code,
            status.HTTP_401_UNAUTHORIZED,
            passed
        )
    
    def run_all_tests(self):
        """Run all cross-tenant access denial tests."""
        print("\n" * 2)
        print("=" * 80)
        print("CROSS-TENANT ACCESS DENIAL INTEGRATION TESTS")
        print("=" * 80)
        
        try:
            self.setup_test_data()
            
            # Run all tests
            self.test_assessment_list_isolation()
            self.test_assessment_detail_cross_tenant_deny()
            self.test_review_list_isolation()
            self.test_review_detail_cross_tenant_deny()
            self.test_template_list_isolation()
            self.test_template_detail_cross_tenant_deny()
            self.test_vendor_list_isolation()
            self.test_vendor_detail_cross_tenant_deny()
            self.test_evidence_list_isolation()
            self.test_evidence_detail_cross_tenant_deny()
            self.test_response_list_isolation()
            self.test_response_detail_cross_tenant_deny()
            self.test_cross_tenant_update_denied()
            self.test_cross_tenant_delete_denied()
            self.test_unauthenticated_access_denied()
            
        except Exception as e:
            print(f"\n❌ EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Print summary
        print("\n" * 2)
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        total = self.test_results['passed'] + self.test_results['failed']
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            print("\nFailed Tests:")
            for error in self.test_results['errors']:
                print(f"  - {error['test']}")
                print(f"    Got: {error['status_code']}, Expected: {error['expected']}")
                if error['details']:
                    print(f"    {error['details']}")
        
        print("=" * 80)
        
        return self.test_results['failed'] == 0


if __name__ == '__main__':
    tester = TestCrossTenantAccessDenial()
    success = tester.run_all_tests()
    exit(0 if success else 1)
