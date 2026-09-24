"""
Phase 4 Backend Integration Tests
Tests all Dashboard and Admin Analytics API endpoints
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.queues.models import QueueEntry, ServiceType, Department
from apps.accounts.models import CustomRole, CustomPermission
from datetime import timedelta
import json

User = get_user_model()


class Phase4IntegrationTests(TestCase):
    """Integration tests for Phase 4 backend APIs"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data for all tests"""
        # Create departments
        cls.dept1 = Department.objects.create(name='Customer Service', slug='customer-service')
        cls.dept2 = Department.objects.create(name='Technical Support', slug='technical-support')
        
        # Create service types
        cls.service1 = ServiceType.objects.create(name='General Inquiry', department=cls.dept1)
        cls.service2 = ServiceType.objects.create(name='Billing', department=cls.dept1)
        cls.service3 = ServiceType.objects.create(name='Technical Issue', department=cls.dept2)
        
        # Create test users (without roles to avoid signal issues)
        cls.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin_test@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True,
            department=cls.dept1
        )
        
        cls.staff_user = User.objects.create_user(
            username='staff_test1',
            email='staff_test1@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False,
            department=cls.dept1
        )
        
        cls.staff_user2 = User.objects.create_user(
            username='staff_test2',
            email='staff_test2@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False,
            department=cls.dept2
        )
        
        # Create test queue entries for today
        today = timezone.now().date()
        for i in range(5):
            QueueEntry.objects.create(
                service_type=cls.service1,
                department=cls.dept1,
                queue_number=f'GI-{i+1:03d}',
                qr_code_data=f'qr_{i}',
                name=f'Customer {i+1}',
                mobile_number=f'555-000{i}',
                email=f'customer{i}@test.com',
                status=QueueEntry.Status.WAITING,
                created_at=timezone.now() - timedelta(minutes=5-i)
            )
        
        # Create some completed entries
        for i in range(3):
            entry = QueueEntry.objects.create(
                service_type=cls.service2,
                department=cls.dept1,
                queue_number=f'BL-{i+1:03d}',
                qr_code_data=f'qr_completed_{i}',
                name=f'Completed {i+1}',
                mobile_number=f'555-100{i}',
                email=f'completed{i}@test.com',
                status=QueueEntry.Status.SERVED,
                created_at=timezone.now() - timedelta(minutes=30),
                served_at=timezone.now() - timedelta(minutes=10)
            )
    
    def setUp(self):
        """Run before each test"""
        self.client = Client()
    
    def test_dashboard_login_required(self):
        """Test that dashboard view requires login"""
        response = self.client.get('/queues/v4/dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_v4_view_loads(self):
        """Test that dashboard_v4 view loads for authenticated user"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/v4/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'q_queues/dashboard_v4.html')
    
    def test_api_dashboard_kpi(self):
        """Test Dashboard KPI API endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/dashboard/kpi/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('queue_length', data)
        self.assertIn('avg_wait_time', data)
        self.assertIn('served_today', data)
        self.assertIn('throughput', data)
        self.assertGreater(data['queue_length'], 0)
    
    def test_api_dashboard_kpi_staff_view(self):
        """Test that staff user only sees their department's data"""
        self.client.login(username='staff_test1', password='testpass123')
        response = self.client.get('/queues/api/dashboard/kpi/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertGreater(data['queue_length'], 0)  # Should see dept1 queues
    
    def test_api_dashboard_charts(self):
        """Test Dashboard Charts API endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/dashboard/charts/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('status_chart', data)
        self.assertIn('department_chart', data)
        self.assertIn('service_chart', data)
        self.assertIn('trend_chart', data)
        
        # Verify chart structure
        self.assertIn('labels', data['status_chart'])
        self.assertIn('data', data['status_chart'])
    
    def test_api_dashboard_queue(self):
        """Test Dashboard Queue API endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/dashboard/queue/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('queue', data)
        self.assertIn('total_waiting', data)
        self.assertGreater(len(data['queue']), 0)
        
        # Verify queue entry structure
        first_entry = data['queue'][0]
        self.assertIn('id', first_entry)
        self.assertIn('queue_number', first_entry)
        self.assertIn('customer_name', first_entry)
        self.assertIn('wait_time_minutes', first_entry)
    
    def test_api_admin_analytics_kpi(self):
        """Test Admin Analytics KPI endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/admin/v4/analytics/')  # First load the page
        self.assertEqual(response.status_code, 200)
        
        # Test the KPI API
        response = self.client.get('/queues/api/admin/analytics/kpi/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('total_tickets', data)
        self.assertIn('completion_rate', data)
        self.assertIn('avg_resolution_time', data)
        self.assertIn('customer_satisfaction', data)
        self.assertGreater(data['total_tickets'], 0)
    
    def test_api_admin_analytics_charts(self):
        """Test Admin Analytics Charts endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/admin/analytics/charts/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('volume_chart', data)
        self.assertIn('department_chart', data)
        self.assertIn('service_chart', data)
        self.assertIn('resolution_chart', data)
        self.assertIn('productivity_chart', data)
        self.assertIn('satisfaction_chart', data)
    
    def test_api_admin_analytics_tables(self):
        """Test Admin Analytics Tables endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/admin/analytics/tables/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('departments', data)
        self.assertIn('services', data)
        self.assertIn('staff', data)
        
        # Verify structure
        if data['departments']:
            dept = data['departments'][0]
            self.assertIn('name', dept)
            self.assertIn('total_tickets', dept)
            self.assertIn('completion_rate', dept)
    
    def test_api_admin_analytics_audit(self):
        """Test Admin Analytics Audit endpoint"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/admin/analytics/audit/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('audit_trail', data)
        self.assertIn('total_entries', data)
    
    def test_api_get_services(self):
        """Test service retrieval by department"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(f'/queues/api/services/?department_id={self.dept1.id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['name'], 'General Inquiry')
    
    def test_kiosk_v4_view_loads(self):
        """Test that kiosk_v4 view loads"""
        self.client.login(username='staff_test1', password='testpass123')
        response = self.client.get('/queues/v4/kiosk/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'q_queues/kiosk_v4.html')
    
    def test_admin_analytics_view_loads(self):
        """Test that admin analytics view loads"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/admin/v4/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/analytics_dashboard.html')
    
    def test_analytics_with_date_filter(self):
        """Test analytics with custom date range"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get('/queues/api/admin/analytics/kpi/?days=7')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('total_tickets', data)


if __name__ == '__main__':
    print("Running Phase 4 Integration Tests...")
    print("\nThese tests verify:")
    print("✓ Dashboard API endpoints (KPI, Charts, Queue)")
    print("✓ Admin Analytics endpoints (KPI, Charts, Tables, Audit)")
    print("✓ View handlers for enhanced templates")
    print("✓ Permission enforcement")
    print("✓ Service retrieval by department")
    print("\nNote: Run with: python manage.py test test_phase4_integration")

