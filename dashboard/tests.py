from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='pass', tenant_id=1)
        self.client.force_authenticate(user=self.user)

    def test_stats_endpoint(self):
        response = self.client.get('/dashboard/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('total_assessments', response.data)

    def test_activity_endpoint(self):
        response = self.client.get('/dashboard/activity/')
        self.assertEqual(response.status_code, 200)
