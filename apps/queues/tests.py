from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User, CustomRole
from apps.queues.models import Department, ServiceType, QueueEntry
from django.conf import settings
import uuid

class QueueSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Test Dept", slug="test-dept", max_entries_per_day=100)
        self.service = ServiceType.objects.create(
            name="Test Service",
            prefix="TS",
            department=self.dept,
        )
        # Get or create MIS role
        mis_role, _ = CustomRole.objects.get_or_create(
            slug='mis',
            defaults={'name': 'Management Information Systems', 'is_system': True}
        )
        self.staff_user = User.objects.create_user(
            username="staff",
            password="staffpassword",
            custom_role=mis_role,
            department=self.dept
        )

    def test_queue_number_generation(self):
        """Test that queue numbers are generated correctly and increment."""
        num1 = self.service.generate_queue_number()
        QueueEntry.objects.create(
            service_type=self.service,
            department=self.dept,
            queue_number=num1,
            qr_code_data=str(uuid.uuid4())
        )
        num2 = self.service.generate_queue_number()
        self.assertEqual(num1, "TS-1")
        self.assertEqual(num2, "TS-2")

    def test_create_queue_entry_api_key(self):
        """Test API key security for creating queue entries."""
        url = reverse("create_queue_entry")
        
        # Test without API key
        response = self.client.post(url, {"service_type": self.service.id})
        self.assertEqual(response.status_code, 403)

        # Test with valid API key
        response = self.client.post(
            url, 
            {"service_type": self.service.id, "api_key": settings.KIOSK_API_KEY}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(QueueEntry.objects.count(), 1)

    def test_department_capacity_limit(self):
        """Test that department capacity is enforced."""
        self.dept.max_entries_per_day = 1
        self.dept.save()
        
        url = reverse("create_queue_entry")
        # Create first entry
        self.client.post(url, {"service_type": self.service.id, "api_key": settings.KIOSK_API_KEY})
        
        # Try to create second entry
        response = self.client.post(url, {"service_type": self.service.id, "api_key": settings.KIOSK_API_KEY})
        self.assertEqual(response.status_code, 429)
        self.assertIn("capacity reached", response.json()["error"])

    def test_update_queue_entry_staff(self):
        """Test that staff can update queue status."""
        entry = QueueEntry.objects.create(
            service_type=self.service,
            department=self.dept,
            queue_number="TS-1",
            qr_code_data="test-qr"
        )
        
        self.client.login(username="staff", password="staffpassword")
        url = reverse("update_queue_entry", args=[entry.id])
        
        response = self.client.post(url, {"status": QueueEntry.Status.SERVED})
        entry.refresh_from_db()
        self.assertEqual(entry.status, QueueEntry.Status.SERVED)
        self.assertIsNotNone(entry.served_at)

    def test_update_queue_entry_api_key(self):
        """Test that kiosk can update queue status with API key."""
        entry = QueueEntry.objects.create(
            service_type=self.service,
            department=self.dept,
            queue_number="TS-1",
            qr_code_data="test-qr"
        )
        
        url = reverse("update_queue_entry", args=[entry.id])
        
        # Without API key
        response = self.client.post(url, {"status": QueueEntry.Status.SERVED})
        self.assertEqual(response.status_code, 403)

        # With API key
        response = self.client.post(
            url, 
            {"status": QueueEntry.Status.SERVED, "api_key": settings.KIOSK_API_KEY}
        )
        entry.refresh_from_db()
        self.assertEqual(entry.status, QueueEntry.Status.SERVED)
