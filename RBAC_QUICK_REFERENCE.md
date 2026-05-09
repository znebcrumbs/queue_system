# RBAC System - Quick Reference Guide

## Overview
The queue system now has a complete Role-Based Access Control (RBAC) system with database-backed API keys and a full admin UI for managing roles and permissions.

---

## Quick Links

| Function | URL | Permission Required |
|----------|-----|-------------------|
| View all roles | `/accounts/roles/` | `manage_roles` |
| Create new role | `/accounts/roles/create/` | `manage_roles` |
| Edit specific role | `/accounts/roles/<id>/` | `manage_roles` |
| Delete role | `/accounts/roles/<id>/delete/` | `manage_roles` |
| View all permissions | `/accounts/permissions/` | `manage_permissions` |
| Create permission | `/accounts/permissions/create/` | `manage_permissions` |
| Delete permission | `/accounts/permissions/<id>/delete/` | `manage_permissions` |
| Assign role to user | `/accounts/users/<id>/assign-role/` | `manage_users` |

---

## Creating a New Role

1. Go to `/accounts/roles/create/`
2. Fill in:
   - **Role Name**: e.g., "Senior Operator" (required)
   - **Slug**: e.g., "senior_operator" (auto-generated, or enter custom)
   - **Description**: Brief explanation (optional)
3. Click on category headers to select all permissions in that category
4. Use "Select All" button to select all permissions at once
5. Click "Create Role"
6. The permission counter updates in real-time

---

## Editing an Existing Role

1. Go to `/accounts/roles/`
2. Click the edit button (pencil icon) on any role
3. Modify:
   - Name, slug, description (non-system roles only)
   - Permissions by checking/unchecking boxes
   - Active status toggle
4. Click "Save Changes"
5. Changes are logged to the audit trail

**Note:** System roles (ADMIN, REGISTRAR, MIS) cannot be edited through the UI. Modify them via Django admin if needed.

---

## Managing Permissions

### View All Permissions
1. Go to `/accounts/permissions/`
2. See all 30+ built-in permissions organized by category
3. Use search box to filter by name or slug
4. Roles using each permission are displayed

### Create Custom Permission
1. Go to `/accounts/permissions/create/`
2. Fill in:
   - **Name**: Human-readable name
   - **Slug**: Code identifier (auto-generated)
   - **Category**: Select from dropdown
   - **Description**: Explain purpose (optional)
3. Click "Create Permission"

**Naming Convention:**
- Use lowercase with underscores
- Pattern: `action_resource`
- Examples:
  - `view_audit_logs`
  - `export_tickets`
  - `manage_departments`
  - `reset_passwords`

### Delete Custom Permission
1. Go to `/accounts/permissions/`
2. Find the custom permission
3. Click the delete button (trash icon)
4. Cannot delete if permission is used by active roles

**Note:** Built-in permissions cannot be deleted.

---

## Assigning Roles to Users

### Method 1: Direct Assignment
1. Go to `/accounts/users/`
2. Click the user
3. Click "Assign Role" button
4. Select new role
5. See permissions preview
6. Confirm assignment

### Method 2: From User List
1. Go to `/accounts/users/`
2. Find user in table
3. Click "Assign Role" link
4. Follow steps above

**Important:** Users can only have one role at a time. Assigning a new role replaces the previous one.

---

## API Key Management

### Overview
API keys are managed through Django admin and accessed via the database.

### Creating API Keys
1. Login to Django admin (`/admin/`)
2. Go to Accounts → API Keys
3. Click "Add API Key"
4. Leave "Key" blank - it auto-generates on save
5. Set "Is Active" = checked
6. Save
7. Copy the generated key (shown on save)

**Key Format:** URLSafe token, e.g., `abc_DEF-ghi_JKL-mno_PQR`

### Using API Keys
```bash
# In header
curl -H "X-API-Key: abc_DEF-ghi_JKL-mno_PQR" https://api.example.com/api/endpoint

# In query parameter
curl https://api.example.com/api/endpoint?api_key=abc_DEF-ghi_JKL-mno_PQR
```

### Managing Keys
- **Disable Key:** Uncheck "Is Active" (doesn't delete, just disables)
- **View Usage:** Check "Last Used At" timestamp
- **Track Owner:** "Created By" shows which admin created it

### Key Rotation
1. Create new API key
2. Update client to use new key
3. Disable old key
4. Monitor "Last Used At" to confirm old key is no longer used
5. Delete old key when safe

---

## System Roles

Three system roles come pre-configured:

### 1. ADMIN
- Full system access
- Can manage all roles and permissions
- Can access all data
- Cannot be deleted or modified via UI

### 2. REGISTRAR  
- Queue management access
- User registration
- Basic reporting
- Cannot be deleted or modified via UI

### 3. MIS
- Reports and analytics
- Data export
- User management
- Cannot be deleted or modified via UI

---

## Permission Categories

### 📊 Dashboard & Analytics
- `view_dashboard`
- `view_analytics`
- `export_reports`
- `export_advanced_reports`

### 🎫 Ticket Management
- `create_tickets`
- `view_tickets`
- `edit_tickets`
- `close_tickets`
- `manage_priorities`

### 📋 Queue Management
- `view_queues`
- `create_queues`
- `manage_queues`
- `manage_services`

### 👥 User Management
- `view_users`
- `create_users`
- `edit_users`
- `delete_users`
- `manage_users`
- `manage_roles`
- `manage_permissions`

### ⚙️ System Configuration
- `manage_settings`
- `manage_departments`
- `configure_system`

### 🔐 Audit & Security
- `view_audit_logs`
- `manage_audit_logs`
- `manage_api_keys`

### 📤 Data Export & Import
- `export_data`
- `import_data`
- `bulk_operations`

---

## Common Tasks

### Add a New Admin User
1. Create user account
2. Go to user detail page
3. Assign role: Select "ADMIN"
4. Click "Assign Role"
5. User now has full system access

### Create a Limited Manager Role
1. Go to `/accounts/roles/create/`
2. Name: "Manager"
3. Select permissions:
   - ✅ `view_dashboard`
   - ✅ `view_queues`
   - ✅ `manage_queues`
   - ✅ `manage_departments`
   - ✅ `view_users`
4. Create role
5. Assign to manager users

### Remove a User's Access
1. Go to user detail page
2. Note current role
3. Create or assign "No Access" role with no permissions
4. Or disable user account via "Is Active" checkbox

### Track API Usage
1. Go to Django admin → API Keys
2. Check "Last Used At" timestamp
3. Sort by date to see recently used keys
4. Disable unused keys for security

---

## Best Practices

### Security
✅ Do: Use strong slug names that indicate purpose
✅ Do: Regularly review and update permissions
✅ Do: Disable unused API keys
✅ Do: Audit role assignments regularly
✅ Do: Keep system roles unchanged
❌ Don't: Give every user ADMIN role
❌ Don't: Create overlapping permissions
❌ Don't: Share API keys between clients

### Role Design
✅ Create roles by job function (Manager, Operator, etc.)
✅ Start with minimal permissions and add as needed
✅ Document role purpose in description field
✅ Review and update quarterly
✅ Use consistent naming conventions

### Permission Naming
✅ Use `action_resource` format
✅ Use lowercase with underscores
✅ Be specific: `edit_own_tickets` not just `edit`
✅ Include context in description

---

## Troubleshooting

### "Permission Denied" on Role Page
- Check user has `manage_roles` permission
- Verify user's role has this permission assigned
- Check AuditLog for permission cache issues

### Cannot Delete Role
- Check if users are assigned to this role
- Cannot delete roles with assigned users
- Reassign users first, then delete

### Cannot Create Duplicate Slug
- Slugs must be unique within system
- Add suffix: `manager_v2`, `operator_new`
- Check existing roles for similar names

### API Key Not Working
- Verify key is active (not disabled)
- Check key format matches URLSafe token
- Verify headers or query parameter syntax
- Check "Last Used At" to confirm key was recognized

---

## Related Documentation

- [PRIORITY_1_FIXES_COMPLETE.md](PRIORITY_1_FIXES_COMPLETE.md) - Technical details of RBAC implementation
- [ACCOUNTS_APP_REVIEW.md](ACCOUNTS_APP_REVIEW.md) - Complete accounts app review with all recommendations
- [QA_TESTING_GUIDE.md](QA_TESTING_GUIDE.md) - Testing procedures for RBAC system

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review PRIORITY_1_FIXES_COMPLETE.md for technical details
3. Check AuditLog in Django admin for permission-related events
4. Check browser console for JavaScript errors

---

**Last Updated:** Phase 4 - RBAC Implementation Complete
