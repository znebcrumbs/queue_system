# QA Testing Guide - Queues Model
## Comprehensive Test Execution Plan

**Generated**: May 2, 2026  
**Project**: Queue Management System  
**Scope**: Full QA testing for Queues app

---

## STATUS SUMMARY

### Test Infrastructure
- ⚠️ Unit tests BROKEN (5/5 tests failing)
  - Root cause: Audit signal references non-existent User.role attribute
  - Must fix before any testing can proceed

### Coverage Baseline
- API Endpoints: 13 major endpoints
- Data Models: 4 models (QueueEntry, ServiceType, Department, Ticket)
- Views: 20+ view functions
- Frontend: 3 major templates + 5 JavaScript modules

---

## PHASE 1: FIX CRITICAL ISSUES (BLOCKER)

### Fix Test Infrastructure
**Priority**: BLOCKER

```python
# Issue: apps/audit/signals.py line 77
# Current Code:
def log_user_change(sender, instance, **kwargs):
    'role': instance.role,  # ❌ FAILS - User doesn't have 'role'

# Fix: Check for attribute existence
def log_user_change(sender, instance, **kwargs):
    'role': getattr(instance, 'role', getattr(instance, 'custom_role', None)),
```

**Test Action**: After fix, run:
```bash
python manage.py test apps.queues -v 2
# Expected: 5/5 tests pass
```

---

## PHASE 2: API ENDPOINT TESTING

### 2.1 Public Kiosk Endpoints

#### Test: Create Queue Entry Public (POST `/queues/create-public/`)

**Test Case 1: Valid Request - Success**
```
Description: Create valid queue entry with all fields
Precondition: Department "Registration" exists, ServiceType "New Registration" exists
Steps:
1. POST /queues/create-public/
2. Body (JSON):
   {
     "service_type_id": 1,
     "customer_name": "John Doe",
     "customer_phone": "0771234567",
     "customer_email": "john@example.com",
     "customer_id": "REG12345"
   }
Expected Result:
- Status: 201
- Response:
  {
    "id": <entry_id>,
    "queue_number": "NR-001",
    "ticket_number": "NR-001",
    "status": "WAITING",
    "qr_code_url": "/queues/qr/<entry_id>/"
  }
- QueueEntry created in database
- AuditLog entry created with action TICKET_CREATED
```

**Test Case 2: Missing Required Field - Failure**
```
Description: Try to create without service_type_id
Steps:
1. POST /queues/create-public/
2. Body (JSON):
   {
     "customer_name": "John Doe"
   }
Expected Result:
- Status: 400
- Response: {"error": "Missing service_type_id"}
```

**Test Case 3: Rate Limiting - Throttle After 10 Requests**
```
Description: Verify 10 req/min throttle is enforced
Steps:
1. Send 11 POST requests to /queues/create-public/ from same IP
2. First 10 should succeed
3. 11th should be throttled
Expected Result:
- Requests 1-10: Status 201
- Request 11: Status 429
- Response: {"error": "Rate limit exceeded..."}
```

**Test Case 4: Department Capacity Reached - Failure**
```
Description: Exceed department's max_entries_per_day
Precondition: Department max_entries_per_day = 5, already 5 entries created today
Steps:
1. POST /queues/create-public/ (6th entry)
Expected Result:
- Status: 429
- Response: {"error": "Department capacity reached for today."}
```

**Test Case 5: Race Condition - Multiple Simultaneous Requests**
```
Description: Test retry logic when capacity check fails
Steps:
1. Set department max_entries_per_day = 100
2. Send 5 concurrent POST requests
3. Verify queue numbers are sequential without duplicates
Expected Result:
- All 5 requests succeed
- Queue numbers: NR-001, NR-002, NR-003, NR-004, NR-005
- No duplicates in database
```

**Test Case 6: Email Validation - Invalid Email**
```
Description: Submit form with invalid email
Steps:
1. POST /queues/create-public/ with email = "invalid-email"
Expected Result:
- Entry created (email field is optional)
- Or API validates and rejects with 400
```

---

### 2.2 Update Queue Entry Endpoint (POST/GET `/queues/update/<entry_id>/`)

**Test Case 7: Staff Update - Authenticated User**
```
Description: Staff user updates ticket status to SERVED
Precondition: 
- Authenticated staff user with permission 'complete_tickets'
- Queue entry in WAITING status
Steps:
1. POST /queues/update/1/ 
2. Body: status=SERVED
Expected Result:
- Status: 302 (redirect) or 200 (AJAX)
- Entry.status = SERVED
- Entry.served_at = current timestamp (not NULL)
- AuditLog entry created with action QUEUE_ENTRY_UPDATED
```

**Test Case 8: Kiosk Update - API Key**
```
Description: Kiosk updates ticket status with API key
Precondition:
- Valid X-KIOSK-API-KEY in settings
- Queue entry in WAITING status
Steps:
1. POST /queues/update/1/
2. Headers: X-KIOSK-API-KEY: <valid_key>
3. Body: status=SERVED
Expected Result:
- Status: 200 or 302
- Entry.status = SERVED
- AuditLog entry created with action API_KEY_USED
```

**Test Case 9: Permission Denied - Unauthorized**
```
Description: User without permission tries to update
Precondition: User doesn't have 'complete_tickets' or 'manage_queues' permission
Steps:
1. POST /queues/update/1/
2. Body: status=SERVED
Expected Result:
- Status: 403
- Response: {"error": "Permission denied"}
- AuditLog entry created with action PERMISSION_DENIED
```

**Test Case 10: Invalid Status Transition**
```
Description: Try to set invalid status
Steps:
1. POST /queues/update/1/
2. Body: status=INVALID_STATUS
Expected Result:
- Entry status unchanged
- Should validate against Status choices
```

---

### 2.3 Dashboard API Endpoints

#### Test: KPI Endpoint (GET `/queues/api/dashboard/kpi/`)

**Test Case 11: KPI Calculation - Single Department**
```
Description: Verify KPI calculations are accurate
Precondition:
- Create 5 WAITING entries
- Create 3 SERVED entries with served_at = created_at + 10 minutes
- Authenticated staff user with view_dashboard permission
Steps:
1. GET /queues/api/dashboard/kpi/
Expected Result:
- Status: 200
- Response:
  {
    "queue_length": 5,
    "avg_wait_time": 10,
    "served_today": 3,
    "throughput": <calculated>,
    "total_today": 8
  }
```

**Test Case 12: KPI for Admin - All Departments**
```
Description: Admin sees system-wide KPIs
Precondition:
- 2 departments with entries
- User has configure_system permission
Steps:
1. GET /queues/api/dashboard/kpi/
Expected Result:
- Includes entries from all departments
- No filtering by user.department
```

**Test Case 13: KPI for Staff - Department Only**
```
Description: Staff sees only their department's KPIs
Precondition:
- 2 departments exist
- User assigned to department A
- Entries in both departments
Steps:
1. GET /queues/api/dashboard/kpi/
Expected Result:
- Only counts entries from user's department
- Ignores entries in other departments
```

---

#### Test: Charts Endpoint (GET `/queues/api/dashboard/charts/`)

**Test Case 14: Charts Data Structure**
```
Description: Verify 4 charts are returned with correct data
Steps:
1. GET /queues/api/dashboard/charts/
Expected Result:
- Status: 200
- Response contains 4 keys:
  1. status_chart: pie chart data
  2. department_chart: bar chart data  
  3. service_chart: pie chart data
  4. trend_chart: line chart (24-hour wait times)
- Each chart has: labels[], data[], colors[]
```

**Test Case 15: Wait Time Trend - 24 Hour Average**
```
Description: Verify trend calculation includes last 24 hours
Precondition: Entries with served_at times spanning past 24 hours
Steps:
1. GET /queues/api/dashboard/charts/
2. Check trend_chart data
Expected Result:
- 24 data points (one per hour)
- Each point = average wait time for that hour
- Format: [0, 5, 3, 7, ...] (minutes)
```

---

### 2.4 Admin Analytics Endpoints

#### Test: Admin KPI (GET `/queues/api/admin/analytics/kpi/?days=30`)

**Test Case 16: System-Wide KPI Calculation**
```
Description: Admin KPIs across all departments/services
Precondition:
- 100+ entries in past 30 days
- Various statuses
- SurveyResponse entries with ratings
Steps:
1. GET /queues/api/admin/analytics/kpi/?days=30
Expected Result:
- Status: 200
- Response:
  {
    "total_tickets": 100,
    "completion_rate": <percentage>,
    "avg_resolution_time": <minutes>,
    "customer_satisfaction": <rating 1-5>
  }
```

**Test Case 17: Admin Analytics - Different Time Ranges**
```
Description: Test days parameter
Steps:
1. GET /queues/api/admin/analytics/kpi/?days=7
2. GET /queues/api/admin/analytics/kpi/?days=90
Expected Result:
- Each returns correct subset based on date range
- Error handling for invalid days parameter
```

---

## PHASE 3: DATA PIPELINE TESTING

### 3.1 Queue Number Generation

**Test Case 18: Queue Number Format**
```
Description: Verify queue number format is consistent
Precondition: ServiceType with prefix="REG"
Steps:
1. Create entry 1
2. Create entry 2
Expected Result:
- Entry 1: queue_number = "REG-001" (with leading zeros)
- Entry 2: queue_number = "REG-002"
- Format: DIGITS-ZEROS (consistent 3-digit counter)
```

**Test Case 19: Queue Number Daily Reset**
```
Description: Verify queue numbers reset daily
Precondition: Set system date/time
Steps:
1. Create entries on Day 1 (count reaches 10)
2. Advance date to Day 2
3. Create new entry on Day 2
Expected Result:
- Day 1, Entry 10: "REG-010"
- Day 2, Entry 1: "REG-001" (reset to 1)
```

**Test Case 20: Queue Number Rollover at 256**
```
Description: Verify rollover behavior (modulo 256)
Precondition: Create 260 entries in single day
Steps:
1. Create 260 entries with same service type on same day
2. Query entries and check queue numbers
Expected Result:
- Entry 256: "REG-256"
- Entry 257: "REG-001" (rollover to 1)
- Entry 258: "REG-002"
- Verify NO DUPLICATES in database (constraint enforced)
```

**Test Case 21: Concurrent Queue Number Generation**
```
Description: Test thread safety of queue number generation
Precondition: Multi-threaded request handler
Steps:
1. Spawn 10 concurrent requests to /queues/create-public/
2. All for same service type, same day
Expected Result:
- 10 entries created
- Queue numbers: 001-010 (no duplicates, no gaps)
- Constraint prevents race condition duplicates
```

---

### 3.2 Timestamp & Wait Time Calculations

**Test Case 22: Wait Time Calculation**
```
Description: Calculate wait time from created_at to served_at
Precondition:
- Entry created at 10:00 AM
- Entry served at 10:15 AM (15 minutes later)
Steps:
1. Create entry
2. Query via API or directly
Expected Result:
- From api_dashboard_kpi: avg_wait_time = 15
- From QueueEntry: (served_at - created_at) / 60 = 15 minutes
```

**Test Case 23: Timezone Boundary Test**
```
Description: Test date calculation near midnight
Precondition: Entry created at 11:59 PM, served at 12:01 AM next day
Steps:
1. Create entry at 11:59 PM
2. Query created_at__date = today
3. Move to next day
4. Query created_at__date = today
Expected Result:
- Created entry counts toward current day (where it was created)
- Query boundaries handle timezone correctly
```

---

### 3.3 Aggregation Performance

**Test Case 24: Department Selection N+1 Query Test**
```
Description: Verify no N+1 queries in department_selection view
Precondition:
- 20 departments
- Each with 5-10 queue entries
Steps:
1. Load /queues/departments/
2. Use Django Debug Toolbar or logging to count queries
Expected Result:
- Should use ~3-5 queries (not 40+)
- Queries: Department.objects.all(), prefetch related data
- OR: Use select_related/prefetch_related to load in 1-2 queries
```

**Test Case 25: Dashboard Analytics Query Count**
```
Description: Measure query efficiency for dashboard charts
Steps:
1. GET /queues/api/dashboard/charts/
2. Count database queries executed
Expected Result:
- Target: < 10 queries
- Current: Likely 24+ (hour loop issue)
- Action Item: Use aggregation or caching
```

---

## PHASE 4: VIEW & FORM TESTING

### 4.1 Frontend Kiosk Form

**Test Case 26: Multi-Step Form Navigation**
```
Description: Test step progression
Steps:
1. Load /queues/kiosk/
2. Verify Step 1 shows: Department dropdown, Service buttons
3. Click Continue → Step 2 shows: Customer info fields
4. Click Back → Return to Step 1
5. Click Continue → Step 3 shows: Confirmation review
Expected Result:
- Step transitions work smoothly
- Progress indicator updates
- Form data persists across steps
```

**Test Case 27: Form Validation - Client Side**
```
Description: Test JavaScript validation before submit
Steps:
1. Try to progress from Step 1 without selecting department
2. Try to progress from Step 2 without entering name
3. Try to submit with invalid email
Expected Result:
- Warning toast appears: "Please fill all required fields"
- Form does not proceed
- Focus moves to invalid field
```

**Test Case 28: Form Submission Success**
```
Description: Test full form submission flow
Steps:
1. Complete all 3 steps with valid data
2. Click "Create Ticket"
Expected Result:
- POST to /queues/create-public/
- On success (201):
  - Show success message
  - Display queue number (e.g., "ST-001")
  - Show QR code
  - Display ticket page
- Timing: < 2 seconds
```

**Test Case 29: Form Network Error Handling**
```
Description: Test error handling if server is unreachable
Steps:
1. Block network requests (dev tools)
2. Try to submit form
Expected Result:
- Error toast: "Network error"
- Retry button appears
- Form data is preserved
```

---

### 4.2 Staff Dashboard

**Test Case 30: Dashboard Load and Polling**
```
Description: Verify dashboard loads and updates in real-time
Precondition: Authenticated staff user with view_dashboard permission
Steps:
1. Load /queues/dashboard/
2. Observe KPI cards update
3. Wait 5+ seconds and verify auto-refresh
4. Switch browser tab, wait 10s, switch back
Expected Result:
- Dashboard loads in < 2 seconds
- KPI values display correctly
- Charts render without errors
- Polling pauses when tab hidden (visibility API)
- Polling resumes when tab visible
```

**Test Case 31: Department Filter**
```
Description: Admin can filter by department
Precondition: Admin user with configure_system permission
Steps:
1. Load dashboard
2. Select different department from filter dropdown
3. Verify KPIs and charts update for that department
Expected Result:
- Filter dropdown appears for admin only
- Chart data filtered to selected department
- Staff user does NOT see filter (locked to their dept)
```

---

### 4.3 Customer Ticket Display

**Test Case 32: Ticket Real-Time Status Updates**
```
Description: Customer ticket page shows live status
Precondition: Entry at /queues/ticket/1/
Steps:
1. Load customer ticket page
2. In staff dashboard, mark ticket as SERVED
3. Customer page should auto-update within 5 seconds
Expected Result:
- Status changes: "Your ticket is being served"
- Next 2 in queue are displayed
- Audio ding plays (if enabled)
- QR code displays correctly
```

**Test Case 33: QR Code Generation**
```
Description: QR code links to ticket display
Steps:
1. Generate QR for entry ID 1: GET /queues/qr/1/
2. Scan QR code or decode manually
Expected Result:
- Returns PNG image
- Content-Type: image/png
- QR encodes URL: /queues/ticket/1/
- QR decodes to valid URL
```

---

## PHASE 5: SECURITY TESTING

### 5.1 Authentication & Authorization

**Test Case 34: Unauthenticated Access to Protected Endpoints**
```
Description: Verify login required
Steps:
1. Access /queues/dashboard/ without login
2. Access /queues/api/dashboard/kpi/ without login
Expected Result:
- Status: 302 (redirect to login) or 403
- Redirected to /accounts/login/
```

**Test Case 35: Permission Enforcement**
```
Description: User without permission cannot access
Precondition: User has no 'view_dashboard' permission
Steps:
1. POST /queues/api/dashboard/kpi/
Expected Result:
- Status: 403
- Response: {"error": "Permission denied"} or similar
- AuditLog entry created with action PERMISSION_DENIED
```

**Test Case 36: API Key Validation**
```
Description: Invalid API key rejected
Steps:
1. POST /queues/update/1/ 
2. Headers: X-KIOSK-API-KEY: invalid-key-12345
Expected Result:
- Status: 403
- Response: {"error": "Unauthorized: Invalid or missing API Key"}
- AuditLog entry created with action UNAUTHORIZED_ACCESS
```

---

### 5.2 Data Privacy

**Test Case 37: Department Isolation**
```
Description: Staff only sees their department data
Precondition:
- Staff user assigned to Department A
- Entries exist in Department A and B
Steps:
1. GET /queues/api/dashboard/kpi/
2. Check response
Expected Result:
- Only includes Department A data
- Ignores Department B entries
```

**Test Case 38: CSV Export Authorization**
```
Description: Only export_data permission can export
Precondition: User without export_data permission
Steps:
1. GET /queues/reports/queues.csv
Expected Result:
- Status: 403 (permission denied)
- OR redirects to login if not authenticated
```

---

## PHASE 6: PERFORMANCE TESTING

### 6.1 Load Testing

**Test Case 39: Dashboard with Large Queue**
```
Description: Dashboard performance with 1000 waiting entries
Precondition: 1000 QueueEntry records with status=WAITING
Steps:
1. GET /queues/api/dashboard/queue/
2. Measure response time
Expected Result:
- Response time: < 2 seconds
- Returns max 10 entries (not all 1000)
- Memory usage reasonable
```

**Test Case 40: Analytics with Large Date Range**
```
Description: Admin analytics with 1 year of data
Precondition: 10,000+ entries in system
Steps:
1. GET /queues/api/admin/analytics/charts/?days=365
2. Measure response time and resource usage
Expected Result:
- Response time: < 5 seconds
- Uses efficient aggregation (not Python loops)
- No memory spikes
```

**Test Case 41: Concurrent Kiosk Users**
```
Description: Load test kiosk endpoint with multiple users
Precondition: Apache JMeter or similar tool
Steps:
1. Simulate 50 concurrent users creating tickets
2. Run for 60 seconds
3. Monitor response times, error rates
Expected Result:
- All requests complete successfully
- Response times: p95 < 2 seconds
- Error rate: 0%
- Server CPU/Memory normal
```

---

## PHASE 7: DATA INTEGRITY TESTING

### 7.1 Database Constraints

**Test Case 42: Queue Number Uniqueness**
```
Description: Duplicate queue numbers cannot exist (same day)
Steps:
1. Attempt to manually create duplicate QueueEntry with same queue_number, service_type, created_at
Expected Result:
- Database raises IntegrityError
- Constraint: unique_queue_per_service_per_day is enforced
```

**Test Case 43: Required Fields Validation**
```
Description: Cannot create entries without required fields
Steps:
1. Try to create QueueEntry without service_type
2. Try to create without queue_number
3. Try to create without created_at
Expected Result:
- Each raises IntegrityError or ValidationError
- Required fields are actually enforced
```

---

### 7.2 Audit Trail Integrity

**Test Case 44: Audit Logging on Create**
```
Description: Ticket creation logged
Steps:
1. Create queue entry via /queues/create-public/
2. Query AuditLog for TICKET_CREATED action
Expected Result:
- AuditLog entry exists
- Fields populated: user, action, object_name, new_values
- Timestamp matches entry creation
```

**Test Case 45: Audit Logging on Update**
```
Description: Status updates logged
Steps:
1. Update entry status from WAITING to SERVED
2. Query AuditLog for QUEUE_ENTRY_UPDATED action
Expected Result:
- AuditLog entry exists
- old_values: {status: WAITING}
- new_values: {status: SERVED}
- user: logged in staff user
```

---

## AUTOMATED TEST SCRIPT TEMPLATE

```python
# tests/test_queues_qa.py

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from apps.queues.models import QueueEntry, ServiceType, Department
from apps.survey.models import SurveyResponse
from django.utils import timezone
from datetime import timedelta
import json

class QueuesAPITestCase(TestCase):
    """Comprehensive QA tests for Queues API"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test department
        self.dept = Department.objects.create(
            name="Test Department",
            slug="test-dept",
            max_entries_per_day=100
        )
        
        # Create test service
        self.service = ServiceType.objects.create(
            name="Test Service",
            prefix="TST",
            department=self.dept
        )
        
        # Create test user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='password123'
        )
        self.staff_user.department = self.dept
        self.staff_user.save()
    
    def test_queue_entry_creation_success(self):
        """Test: Create Queue Entry Public - Success"""
        data = {
            'service_type_id': self.service.id,
            'customer_name': 'John Doe',
            'customer_phone': '0771234567',
            'customer_email': 'john@test.com',
        }
        
        response = self.client.post('/queues/create-public/', data)
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.json())
        self.assertIn('queue_number', response.json())
        self.assertTrue(QueueEntry.objects.filter(
            customer_name='John Doe'
        ).exists())
    
    def test_api_dashboard_kpi(self):
        """Test: Dashboard KPI Endpoint"""
        # Create test entries
        for i in range(5):
            QueueEntry.objects.create(
                service_type=self.service,
                queue_number=f'TST-{i:03d}',
                qr_code_data=f'qr-{i}',
                department=self.dept,
                status=QueueEntry.Status.WAITING
            )
        
        # Login and fetch
        self.client.login(username='staff', password='password123')
        response = self.client.get('/queues/api/dashboard/kpi/')
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['queue_length'], 5)
```

---

## TEST EXECUTION CHECKLIST

### Pre-Execution
- [ ] Fix test infrastructure (User.role issue)
- [ ] Set KIOSK_API_KEY in settings
- [ ] Create test departments
- [ ] Create test service types
- [ ] Clear test database

### Execution Order
1. [ ] Phase 1: Fix issues
2. [ ] Phase 2: API endpoints (40 test cases)
3. [ ] Phase 3: Data pipelines (8 test cases)
4. [ ] Phase 4: Views (8 test cases)
5. [ ] Phase 5: Security (5 test cases)
6. [ ] Phase 6: Performance (3 test cases)
7. [ ] Phase 7: Data integrity (3 test cases)

### Post-Execution
- [ ] Document all failures
- [ ] Calculate coverage percentage
- [ ] Create tickets for bugs
- [ ] Sign-off from QA lead

---

## SUCCESS CRITERIA

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Test Pass Rate | 100% | 0% (broken) | ❌ |
| API Response Time | <500ms | ? | ⏳ |
| Dashboard Load Time | <2s | ? | ⏳ |
| Concurrent Users | 100+ | ? | ⏳ |
| Code Coverage | >80% | ? | ⏳ |
| Security Issues | 0 critical | 3+ | ❌ |

---

## RESOURCES NEEDED

- Python 3.10+
- Django test client
- Apache JMeter (performance testing)
- Postman (API testing)
- Browser dev tools
- Database backup
- Staging environment

---

## SIGN-OFF

- QA Lead: _______________ Date: _______
- Dev Lead: _______________ Date: _______
- Product Owner: _______________ Date: _______

