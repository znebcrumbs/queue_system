# Comprehensive QA Report: Queues Model

**Date**: May 2, 2026  
**Scope**: Full system QA - API endpoints, data pipelines, views, and frontend  
**Status**: IN PROGRESS

---

## 1. API ENDPOINTS VALIDATION

### 1.1 Security & Authentication Issues

#### ⚠️ CRITICAL ISSUES FOUND

**Issue 1: CSRF Exemption on Public Kiosk Endpoint**
- **Location**: [apps/queues/views.py](apps/queues/views.py) - `create_queue_entry_public()` 
- **Severity**: MEDIUM
- **Problem**: 
  ```python
  @csrf_exempt  # Public kiosk form - no CSRF token from kiosk devices
  @throttle_kiosk
  def create_queue_entry_public(request):
  ```
  - CSRF exemption is appropriate for kiosk devices, but should verify this is intended
  - Throttle decorator set to 10 requests/minute - verify if this is sufficient
- **Recommendation**: 
  - ✅ Rate limiting is present but should test under load
  - Consider adding IP-based blocking after N failed attempts

**Issue 2: API Key Validation Not Enforced Universally**
- **Location**: Multiple endpoints - `create_queue_entry()`, `update_queue_entry()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  # create_queue_entry has @api_key_required COMMENTED OUT
  @csrf_exempt
  @throttle_kiosk  # This is present instead
  def create_queue_entry(request):
  ```
  - Comment indicates API key was removed but throttling left
  - Inconsistent protection across endpoints
- **Recommendation**: 
  - Either protect with API key + throttle OR document why throttle alone is sufficient
  - Consider adding authentication/permission checks

**Issue 3: Update Endpoint Accepts Both Authenticated & API Key**
- **Location**: `update_queue_entry()` 
- **Severity**: MEDIUM-HIGH
- **Problem**:
  ```python
  if request.user.is_authenticated:
      if not request.user.has_any_permission('complete_tickets', 'manage_queues'):
          return JsonResponse({"error": "Permission denied"}, status=403)
  else:
      # Check for API key - falls through if valid
      api_key = request.headers.get("X-KIOSK-API-KEY") or ...
  ```
  - Conditional logic could allow unauthorized access if permission check fails but API key is valid
  - No audit logging on successful API key access for updates
- **Testing Needed**:
  - [ ] Test authenticated user with no permission + valid API key = ?
  - [ ] Test unauthenticated with invalid API key
  - [ ] Verify audit logs are created for all status updates

---

### 1.2 Permission & Authorization Issues

#### FINDINGS

**Issue 4: Dashboard API Endpoints Missing Audit Logging**
- **Location**: `api_dashboard_kpi()`, `api_dashboard_charts()`, `api_dashboard_queue()`
- **Severity**: LOW-MEDIUM
- **Problem**: No audit logging for data access
- **Recommendation**:
  ```python
  AuditLog.log(
      action=AuditLog.Action.API_ACCESSED,
      user=request.user,
      object_type='API',
      object_name=f'/api/dashboard/{endpoint}/',
      request=request
  )
  ```

**Issue 5: Admin Analytics Endpoints Need Rate Limiting**
- **Location**: `api_admin_analytics_*()` endpoints
- **Severity**: LOW
- **Problem**: These endpoints can generate complex queries but have no rate limiting
- **Recommendation**: Add throttling decorator for admin endpoints:
  ```python
  @require_permission('configure_system')
  @throttle_kiosk  # Reuse existing throttle
  def api_admin_analytics_charts(request):
  ```

---

### 1.3 Data Validation Issues

#### CRITICAL FINDINGS

**Issue 6: Missing Validation on Queue Number Generation**
- **Location**: `create_queue_entry_public()` - Queue number generation
- **Severity**: MEDIUM
- **Problem**:
  ```python
  queue_number = f"{service_type.name[:2].upper()}-{count_today:03d}"
  ```
  - No leading zeros enforcement - could create "ST-1" and "ST-01" (inconsistent)
  - Format string uses `:03d` but should be `:04d` for safety
  - Retry logic only handles IntegrityError but doesn't validate final result
- **Testing Needed**:
  - [ ] Test queue number generation with 100+ entries - check for duplicates
  - [ ] Test with service type names < 2 characters
  - [ ] Test when count exceeds 256 (rollover behavior)

**Issue 7: Customer Email/Phone Not Required**
- **Location**: `create_queue_entry_public()` - Form submission
- **Severity**: LOW-MEDIUM
- **Problem**:
  ```python
  name = data.get("customer_name")  # No validation
  mobile = data.get("customer_phone")  # Can be None
  email = data.get("customer_email")  # Can be None
  ```
  - No `.POST.get()` defaults or validation
  - QueueEntry model allows blank mobile_number and email
- **Testing Needed**:
  - [ ] Test creating ticket with no phone/email
  - [ ] Test with invalid email format
  - [ ] Test with special characters in name/phone

**Issue 8: Department Capacity Check Race Condition**
- **Location**: `create_queue_entry_public()` 
- **Severity**: HIGH
- **Problem**:
  ```python
  if dept and getattr(dept, "max_entries_per_day", 0) > 0:
      dept_count = QueueEntry.objects.filter(
          department=dept,
          created_at__date=timezone.now().date()
      ).count()
      if dept_count >= dept.max_entries_per_day:
          return JsonResponse({"error": "Department capacity reached"}, status=429)
  # Then: TRANSACTION RETRY LOOP - could bypass capacity check!
  for _ in range(3):
      with transaction.atomic():
          # Recreate count inside transaction
          count_today = QueueEntry.objects.filter(...).count() + 1
  ```
  - Capacity check happens BEFORE transaction
  - Multiple requests could slip through capacity limit
  - Transaction atomic block doesn't re-check capacity
- **Recommended Fix**:
  ```python
  for _ in range(3):
      with transaction.atomic():
          dept_count = QueueEntry.objects.filter(...).count()
          if dept_count >= dept.max_entries_per_day:
              raise IntegrityError()  # Trigger retry
          entry = QueueEntry.objects.create(...)
  ```

---

### 1.4 API Response Format & Documentation

#### ISSUES

**Issue 9: Inconsistent API Response Structure**
- **Location**: Multiple endpoints
- **Severity**: LOW-MEDIUM
- **Problem**: Response formats vary:
  ```python
  # create_queue_entry_public returns:
  {"id": entry.id, "queue_number": entry.queue_number, ...}
  
  # api_dashboard_kpi returns:
  {'queue_length': queue_length, 'avg_wait_time': avg_wait_minutes, ...}
  
  # api_admin_analytics_kpi returns:
  {'total_tickets': total_tickets, 'completion_rate': completion_rate, ...}
  ```
- **Testing Needed**: Document standard response wrapper format
- **Recommendation**: Create consistent wrapper:
  ```python
  {
    "success": true,
    "data": { ... },
    "timestamp": "ISO-8601",
    "errors": []  # When failures occur
  }
  ```

**Issue 10: Missing API Documentation**
- **Severity**: MEDIUM
- **Problem**: No OpenAPI/Swagger documentation
- **Recommendation**: Add docstrings with request/response examples

---

## 2. DATA PIPELINES VALIDATION

### 2.1 Queue Number Generation Pipeline

#### FINDINGS

**Issue 11: Queue Number Format Inconsistency**
- **Location**: `ServiceType.generate_queue_number()` vs `create_queue_entry()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  # In ServiceType model:
  return f"{self.get_prefix()}-{number:01d}"  # Format: "REG-1"
  
  # In views:
  queue_number = f"{service_type.name[:2].upper()}-{count_today:03d}"  # Format: "ST-001"
  ```
  - Two different formatting styles used in codebase
  - `:01d` in model vs `:03d` in views
  - `get_prefix()` not used in views
- **Testing Needed**:
  - [ ] Which format is actually used in production?
  - [ ] Can both formats coexist in same system?
  - [ ] What happens when service type changes prefix?
- **Recommendation**: Standardize - use one approach consistently

**Issue 12: Daily Counter Rollover at 256**
- **Location**: `ServiceType.generate_queue_number()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  number = (count_today % 256) + 1
  ```
  - After 256 entries, counter resets to 1
  - Could create duplicate queue numbers on same day
  - No warning or error when rollover occurs
- **Testing Needed**:
  - [ ] Create 260+ tickets in one day
  - [ ] Verify duplicates don't exist
  - [ ] Check database constraints catch duplicates

---

### 2.2 Timestamp & Duration Calculation Pipeline

#### ISSUES

**Issue 13: Wait Time Calculation Inconsistency**
- **Location**: `Ticket` model vs `api_dashboard_kpi()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  # In Ticket model:
  if self.started_at and not self.wait_time_minutes:
      delta = (self.started_at - self.created_at).total_seconds() / 60
  
  # In API endpoint:
  avg_wait = completed_qs.filter(...).annotate(
      wait_minutes=(F('served_at') - F('created_at'))
  ).aggregate(avg_wait=Avg('wait_minutes'))
  
  # In dashboard chart:
  wait_time = (timezone.now() - entry.created_at).total_seconds() / 60
  ```
  - Three different ways to calculate wait time
  - Some use `started_at`, some use `created_at`, some use `served_at`
  - Inconsistent naming: `wait_time_minutes` vs `wait_minutes`
- **Testing Needed**:
  - [ ] Compare wait times from all three sources for same ticket
  - [ ] Verify which is authoritative
  - [ ] Check database records match calculations

**Issue 14: Timezone Handling in Timestamps**
- **Location**: `timezone.now()` used throughout
- **Severity**: LOW-MEDIUM
- **Problem**:
  - No explicit timezone configuration visible
  - `created_at__date=timezone.now().date()` - potential off-by-one errors if timezone differs
- **Testing Needed**:
  - [ ] Test ticket creation near midnight with timezone changes
  - [ ] Verify date boundaries are correct

---

### 2.3 Data Aggregation Pipelines

#### CRITICAL FINDINGS

**Issue 15: N+1 Query Problem in Department Selection**
- **Location**: `department_selection()` view
- **Severity**: MEDIUM-HIGH
- **Problem**:
  ```python
  departments = Department.objects.all()
  for dept in departments:
      serving = QueueEntry.objects.filter(  # Query in loop!
          department=dept,
          status=QueueEntry.Status.SERVED
      ).order_by('-served_at').first()
      remaining_count = QueueEntry.objects.filter(  # Another query in loop!
          department=dept,
          status=QueueEntry.Status.WAITING
      ).count()
  ```
  - If 20 departments, makes 40+ queries
- **Recommended Fix**:
  ```python
  from django.db.models import Prefetch, Count, Q
  from django.db.models.functions import Count as CountFunc
  
  departments = Department.objects.prefetch_related(
      Prefetch(
          'queueentry_set',
          QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).order_by('-served_at')[:1]
      )
  ).annotate(
      waiting_count=Count('queueentry', filter=Q(queueentry__status=QueueEntry.Status.WAITING))
  )
  ```

**Issue 16: Dashboard Analytics Query Performance**
- **Location**: `api_admin_analytics_charts()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  # Loop through 24 hours, each iteration runs a query:
  for i in range(24, 0, -1):
      segment_start = timezone.now() - timedelta(hours=i)
      segment_end = timezone.now() - timedelta(hours=i-1)
      avg_wait = queue_qs.filter(created_at__gte=segment_start, ...).annotate(...).aggregate(...)
  ```
  - 24 queries for one chart
  - No caching
- **Recommendation**: 
  - Use database aggregation or caching
  - Consider celery background tasks

**Issue 17: Missing Indexes on Frequently Filtered Fields**
- **Location**: `models.py`
- **Severity**: MEDIUM-HIGH
- **Problem**:
  ```python
  # QueueEntry model lacks critical indexes:
  - created_at__date  # Used in most queries
  - department + status  # Common filter combination
  - service_type + created_at
  ```
- **Recommended Fix**:
  ```python
  class Meta:
      indexes = [
          models.Index(fields=['created_at', 'status']),
          models.Index(fields=['department', 'status']),
          models.Index(fields=['service_type', 'created_at']),
          models.Index(fields=['department', 'created_at', 'status']),
      ]
  ```

---

## 3. VIEWS VALIDATION

### 3.1 Authentication & Permission Issues

#### FINDINGS

**Issue 18: Inconsistent Permission Checking**
- **Location**: Various view functions
- **Severity**: MEDIUM
- **Problem**:
  ```python
  # dashboard view:
  @require_permission('view_dashboard')  # Decorator
  def dashboard_v4(request):
  
  # update_queue_entry:
  if not request.user.has_any_permission('complete_tickets', 'manage_queues'):  # Manual check
  
  # queue_list:
  @require_permission('view_tickets')  # Decorator
  ```
  - Mix of decorator-based and manual checks
  - `has_any_permission()` - verify this method exists in User model
- **Testing Needed**:
  - [ ] Verify `has_any_permission()` implementation
  - [ ] Test with each permission combination

**Issue 19: Missing Department Isolation**
- **Location**: `queue_list()`, `dashboard_v4()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  if user.has_permission('configure_system'):  # Admin
      entries = QueueEntry.objects.exclude(...)
  else:  # Staff
      entries = QueueEntry.objects.filter(department=user.department)
  ```
  - If `user.department` is None for staff user, returns empty set
  - No error handling or redirect
- **Testing Needed**:
  - [ ] Test staff user with no department assigned
  - [ ] Verify appropriate error message

---

### 3.2 Error Handling & Edge Cases

#### CRITICAL FINDINGS

**Issue 20: Unhandled IntegrityError in Retry Loop**
- **Location**: `create_queue_entry_public()` 
- **Severity**: HIGH
- **Problem**:
  ```python
  for _ in range(3):
      try:
          with transaction.atomic():
              entry = QueueEntry.objects.create(...)
          return JsonResponse({...}, status=201)
      except IntegrityError:
          logger.debug(f"Retry attempt...")
          continue
  
  return JsonResponse({"error": "Failed to create ticket after retries"}, status=500)
  ```
  - IntegrityError raised but what about other exceptions?
  - Catches bare `IntegrityError` - not imported
  - After 3 retries, returns generic 500 error
- **Testing Needed**:
  - [ ] Force IntegrityError - does retry work?
  - [ ] What exceptions are NOT caught?
  - [ ] Does 500 error get logged properly?

**Issue 21: Missing Validation on QR Code Generation**
- **Location**: `generate_qr()`
- **Severity**: LOW-MEDIUM
- **Problem**:
  ```python
  def generate_qr(request, entry_id):
      entry = get_object_or_404(QueueEntry, id=entry_id)
      ticket_url = request.build_absolute_uri(...)
      qr = qrcode.make(ticket_url)
      buffer = io.BytesIO()
      qr.save(buffer, format="PNG")
      # No exception handling if qrcode.make() fails
  ```
- **Testing Needed**:
  - [ ] What if entry_id doesn't exist (404 is correct)
  - [ ] What if URL generation fails
  - [ ] What if PNG encoding fails

**Issue 22: Department Selection View Not Secure**
- **Location**: `department_selection()`
- **Severity**: LOW
- **Problem**:
  ```python
  def department_selection(request):  # No @login_required
      departments = Department.objects.all()
      for dept in departments:
          # Reveals queue lengths and current service times
  ```
- **Recommendation**: Add `@login_required` or validate access

---

### 3.3 Business Logic Issues

#### FINDINGS

**Issue 23: No Transaction Consistency in Update Operations**
- **Location**: `update_queue_entry()`
- **Severity**: MEDIUM
- **Problem**:
  ```python
  entry.status = status
  if status == QueueEntry.Status.SERVED:
      entry.served_at = timezone.now()
  entry.save()
  # Then separately:
  AuditLog.log(...)  # Outside transaction
  ```
  - Entry and audit log could be out of sync if audit logging fails
  - No atomic update
- **Recommendation**:
  ```python
  with transaction.atomic():
      entry.status = status
      if status == QueueEntry.Status.SERVED:
          entry.served_at = timezone.now()
      entry.save()
      AuditLog.log(...)
  ```

**Issue 24: Print Functionality Has Silent Failure**
- **Location**: `print_ticket()`
- **Severity**: LOW
- **Problem**:
  ```python
  try:
      printer = Usb(0x04b8, 0x0e15)
      # ...
  except Exception:
      # Printer failures shouldn't kill request flow
      pass  # Silent failure
  ```
- **Recommendation**: Log printer failures:
  ```python
  except Exception as e:
      logger.warning(f"Printer error: {str(e)}", exc_info=True)
  ```

---

## 4. FRONTEND VALIDATION

### 4.1 Kiosk Form (Multi-Step)

#### FINDINGS

**Issue 25: No Validation Before Form Submission**
- **Location**: [static/js/kiosk.js](static/js/kiosk.js)
- **Severity**: MEDIUM
- **Problem**: File was truncated in reading, need to verify:
  - [ ] Step 1: Department validation
  - [ ] Step 2: Name, phone, email validation (before/after submit)
  - [ ] Step 3: Final review before POST
- **Testing Needed**: Manual test kiosk form with invalid inputs

**Issue 26: AJAX Form Submission No Error Handling**
- **Location**: Kiosk form submission
- **Severity**: MEDIUM
- **Problem**:
  ```javascript
  // Need to verify submitForm() implementation handles:
  // - Network errors
  // - 429 (rate limit) responses
  // - 400/500 errors
  // - Retry logic
  ```
- **Testing Needed**: Test network failures, rate limiting

---

### 4.2 Dashboard Charts & Real-Time Updates

#### FINDINGS

**Issue 27: Dashboard Polling May Impact Server Performance**
- **Location**: [static/js/dashboard.js](static/js/dashboard.js)
- **Severity**: MEDIUM
- **Problem**:
  ```javascript
  pollInterval: 5000  // 4 API calls every 5 seconds
  // If 50 concurrent users:
  // 200 API requests every 5 seconds = 40 req/sec
  ```
- **Testing Needed**:
  - [ ] Load test with N concurrent users
  - [ ] Monitor database query load
  - [ ] Check if charts update smoothly

**Issue 28: Chart.js Configuration Not Visible**
- **Location**: [static/js/dashboard.js](static/js/dashboard.js)
- **Severity**: LOW
- **Problem**: Need to verify:
  - [ ] Charts are responsive
  - [ ] Memory leaks on chart re-render
  - [ ] Data point limits (don't load 1000+ points)

---

### 4.3 Ticket Display (Customer View)

#### FINDINGS

**Issue 29: Real-Time Status Updates Not Visible**
- **Location**: [templates/q_queues/ticket.html](templates/q_queues/ticket.html)
- **Severity**: MEDIUM
- **Problem**: Need to verify:
  - [ ] Does page poll for status updates?
  - [ ] What interval (5s, 10s, manual refresh)?
  - [ ] HTML5 audio ding when status changes - works on all browsers?

---

## 5. INTEGRATION TESTING CHECKLIST

### End-to-End Flows

- [ ] **Kiosk Flow**: 
  - [ ] Department selection → Service selection → Customer info → Confirm → QR code → Ticket display
  - [ ] Verify queue number appears immediately
  - [ ] Test with capacity limits enforced

- [ ] **Staff Dashboard Flow**:
  - [ ] Login → Department assigned → Dashboard loads → Live KPIs update
  - [ ] Click update status → Ticket moves to served → Customer sees update
  - [ ] Admin sees all departments

- [ ] **Export Flow**:
  - [ ] View reports → Export CSV → Open in Excel → Data is correct

### Data Integrity Tests

- [ ] Create 100+ tickets → Verify no duplicate queue numbers
- [ ] Update ticket status multiple times → Verify audit log consistency
- [ ] Delete department → Verify orphaned queue entries handled
- [ ] Concurrent ticket creation → No race conditions

### Performance Tests

- [ ] Dashboard with 1000 waiting tickets → Still loads in <2s
- [ ] Admin analytics with 30 days of data → Queries complete in <5s
- [ ] 50 concurrent kiosk users → No rate limit false positives

---

## 6. SECURITY AUDIT SUMMARY

### Critical Issues (Fix Immediately)
- [ ] **Issue 8**: Department capacity check race condition
- [ ] **Issue 20**: IntegrityError handling in retry loop
- [ ] **ISSUE 30 (NEW)**: Test Suite Broken - User.role attribute missing
  - **Location**: [apps/audit/signals.py](apps/audit/signals.py) line 77
  - **Severity**: CRITICAL
  - **Problem**: Signal handler references `instance.role` but User model doesn't have this attribute
  - **Impact**: All tests fail during setUp with AttributeError
  - **All 5 existing queue tests failing**:
    - test_create_queue_entry_api_key
    - test_department_capacity_limit
    - test_queue_number_generation
    - test_update_queue_entry_api_key
    - test_update_queue_entry_staff

### High Priority (Fix Before Release)
- [ ] **Issue 2**: Inconsistent API key validation
- [ ] **Issue 15**: N+1 query problem in department selection

### Medium Priority (Address Soon)
- [ ] **Issue 1**: CSRF and rate limiting configuration
- [ ] **Issue 11**: Queue number format inconsistency
- [ ] **Issue 13**: Wait time calculation inconsistency

### Low Priority (Nice to Have)
- [ ] **Issue 9**: Inconsistent API response format
- [ ] **Issue 16**: Dashboard query performance optimization
- [ ] **Issue 25**: Form validation completeness

---

## 7. RECOMMENDATIONS

### Immediate Actions
1. **Fix capacity check race condition** (Issue 8)
2. **Add database indexes** (Issue 17)
3. **Standardize queue number generation** (Issue 11)

### Short Term (This Sprint)
1. Add comprehensive audit logging to all API endpoints
2. Implement API response wrapper format
3. Optimize N+1 queries
4. Add rate limiting to admin endpoints

### Medium Term (Next Quarter)
1. Add API documentation (OpenAPI/Swagger)
2. Implement caching for analytics endpoints
3. Performance testing with load simulation
4. Add database connection pooling

### Long Term (Roadmap)
1. Consider WebSocket for real-time updates instead of polling
2. Add data warehouse for analytics
3. Implement comprehensive API versioning

---

## 8. FILES TO EXAMINE IN DETAIL

- [ ] [apps/queues/models.py](apps/queues/models.py) - Complete review
- [ ] [apps/queues/views.py](apps/queues/views.py) - All endpoints (900+ lines)
- [ ] [static/js/kiosk.js](static/js/kiosk.js) - Form validation logic
- [ ] [static/js/dashboard.js](static/js/dashboard.js) - Polling and chart rendering
- [ ] [templates/q_queues/kiosk_v4.html](templates/q_queues/kiosk_v4.html) - Form template
- [ ] [templates/q_queues/dashboard_v4.html](templates/q_queues/dashboard_v4.html) - Dashboard layout
- [ ] [apps/accounts/decorators.py](apps/accounts/decorators.py) - `require_permission()` implementation

---

## QA Testing Matrix

| Component | Unit Tests | Integration | E2E | Performance | Security |
|-----------|-----------|-------------|-----|-------------|----------|
| Queue Entry Creation | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Status Update | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ |
| Dashboard KPI API | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ |
| Admin Analytics | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Kiosk Form | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| QR Code Generation | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ |
| CSV Export | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ |

**Legend**: ✅ Good | ⚠️ Needs Testing | ❌ Failing

---

## NEXT STEPS

1. **Review this report** with team
2. **Prioritize issues** by severity
3. **Create tickets** for each issue
4. **Execute test cases** from checklist
5. **Run performance tests** on staging
6. **Security review** by dedicated team
7. **Sign off** before production deployment

