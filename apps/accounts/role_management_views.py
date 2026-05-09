"""
Views for managing custom roles and permissions.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.accounts.decorators import require_permission
from apps.audit.models import AuditLog
from .models import CustomRole, CustomPermission, User


@login_required
@require_permission('manage_roles')
def role_list(request):
    """List all custom roles."""
    roles = CustomRole.objects.all()
    
    context = {
        'roles': roles,
        'total_roles': roles.count(),
        'system_roles': roles.filter(is_system=True).count(),
        'custom_roles': roles.filter(is_system=False).count(),
    }
    
    return render(request, 'accounts/role_list.html', context)


@login_required
@require_permission('manage_roles')
def role_detail(request, role_id):
    """View or edit a specific role."""
    role = get_object_or_404(CustomRole, id=role_id)
    
    # Prevent editing system roles (unless superuser)
    if role.is_system and not request.user.is_superuser:
        return redirect('role_list')
    
    if request.method == 'POST':
        old_perms = list(role.permissions.values_list('slug', flat=True))
        
        role.name = request.POST.get('name', role.name)
        role.description = request.POST.get('description', role.description)
        role.is_active = request.POST.get('is_active') == 'on'
        role.save()
        
        # Update permissions
        permission_ids = request.POST.getlist('permissions')
        permissions = CustomPermission.objects.filter(id__in=permission_ids)
        role.permissions.set(permissions)
        
        new_perms = list(permissions.values_list('slug', flat=True))
        
        # Log the change
        AuditLog.log(
            action=AuditLog.Action.SETTINGS_CHANGED,
            user=request.user,
            object_type='CustomRole',
            object_id=role.id,
            object_name=role.name,
            old_values={'permissions': old_perms},
            new_values={'permissions': new_perms},
            description=f"Updated role '{role.name}' permissions",
            request=request
        )
        
        return redirect('role_detail', role_id=role.id)
    
    # Group permissions by category
    all_permissions = CustomPermission.objects.all()
    permissions_by_category = {}
    for perm in all_permissions:
        if perm.category not in permissions_by_category:
            permissions_by_category[perm.category] = []
        permissions_by_category[perm.category].append(perm)
    
    context = {
        'role': role,
        'permissions_by_category': permissions_by_category.items(),
        'user_count': role.users.count(),
        'is_system': role.is_system,
    }
    
    return render(request, 'accounts/role_detail.html', context)


@login_required
@require_permission('manage_roles')
def role_create(request):
    """Create a new custom role."""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        permission_ids = request.POST.getlist('permissions')
        
        # Validate slug
        if CustomRole.objects.filter(slug=slug).exists():
            return render(request, 'accounts/role_form.html', {
                'error': 'A role with this slug already exists',
                'all_permissions': CustomPermission.objects.all(),
            })
        
        # Create role
        role = CustomRole.objects.create(
            name=name,
            slug=slug,
            description=description,
            created_by=request.user,
            is_system=False,
        )
        
        # Assign permissions
        permissions = CustomPermission.objects.filter(id__in=permission_ids)
        role.permissions.set(permissions)
        
        # Log creation
        AuditLog.log(
            action=AuditLog.Action.SETTINGS_CHANGED,
            user=request.user,
            object_type='CustomRole',
            object_id=role.id,
            object_name=role.name,
            new_values={'created': True, 'permissions': list(permissions.values_list('slug', flat=True))},
            description=f"Created custom role '{role.name}'",
            request=request
        )
        
        return redirect('role_detail', role_id=role.id)
    
    # Group permissions by category
    all_permissions = CustomPermission.objects.all()
    permissions_by_category = {}
    for perm in all_permissions:
        if perm.category not in permissions_by_category:
            permissions_by_category[perm.category] = []
        permissions_by_category[perm.category].append(perm)
    
    context = {
        'permissions_by_category': permissions_by_category.items(),
    }
    
    return render(request, 'accounts/role_form.html', context)


@login_required
@require_permission('manage_roles')
def role_delete(request, role_id):
    """Delete a custom role."""
    role = get_object_or_404(CustomRole, id=role_id)
    
    # Prevent deleting system roles
    if role.is_system:
        return redirect('role_list')
    
    # Prevent deleting if users are assigned
    if role.users.exists():
        return render(request, 'accounts/role_list.html', {
            'error': f'Cannot delete role "{role.name}" - it has {role.users.count()} users assigned',
        })
    
    role_name = role.name
    role.delete()
    
    # Log deletion
    AuditLog.log(
        action=AuditLog.Action.SETTINGS_CHANGED,
        user=request.user,
        object_type='CustomRole',
        object_id=0,
        object_name=role_name,
        old_values={'deleted': True},
        description=f"Deleted custom role '{role_name}'",
        request=request
    )
    
    return redirect('role_list')


@login_required
@require_permission('manage_permissions')
def permission_list(request):
    """List all permissions."""
    permissions = CustomPermission.objects.all()
    
    context = {
        'permissions': permissions,
        'total_permissions': permissions.count(),
        'builtin_permissions': permissions.filter(is_builtin=True).count(),
        'custom_permissions': permissions.filter(is_builtin=False).count(),
    }
    
    return render(request, 'accounts/permission_list.html', context)


@login_required
@require_permission('manage_permissions')
def permission_create(request):
    """Create a new custom permission."""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        category = request.POST.get('category', 'custom')
        
        # Validate slug
        if CustomPermission.objects.filter(slug=slug).exists():
            return render(request, 'accounts/permission_form.html', {
                'error': 'A permission with this slug already exists',
                'categories': CustomPermission.CATEGORY_CHOICES,
            })
        
        # Create permission
        permission = CustomPermission.objects.create(
            name=name,
            slug=slug,
            description=description,
            category=category,
            is_builtin=False,
        )
        
        # Log creation
        AuditLog.log(
            action=AuditLog.Action.SETTINGS_CHANGED,
            user=request.user,
            object_type='CustomPermission',
            object_id=permission.id,
            object_name=permission.name,
            new_values={'created': True, 'slug': slug},
            description=f"Created custom permission '{permission.name}'",
            request=request
        )
        
        return redirect('permission_list')
    
    context = {
        'categories': CustomPermission.CATEGORY_CHOICES,
    }
    
    return render(request, 'accounts/permission_form.html', context)


@login_required
@require_permission('manage_permissions')
def permission_delete(request, permission_id):
    """Delete a custom permission."""
    permission = get_object_or_404(CustomPermission, id=permission_id)
    
    # Prevent deleting built-in permissions
    if permission.is_builtin:
        return redirect('permission_list')
    
    # Prevent deleting if roles use it
    if permission.roles.exists():
        return render(request, 'accounts/permission_list.html', {
            'error': f'Cannot delete permission "{permission.name}" - it is used by {permission.roles.count()} roles',
        })
    
    perm_name = permission.name
    permission.delete()
    
    # Log deletion
    AuditLog.log(
        action=AuditLog.Action.SETTINGS_CHANGED,
        user=request.user,
        object_type='CustomPermission',
        object_id=0,
        object_name=perm_name,
        old_values={'deleted': True},
        description=f"Deleted custom permission '{perm_name}'",
        request=request
    )
    
    return redirect('permission_list')


@login_required
@require_permission('manage_users')
def assign_role(request, user_id):
    """Assign a custom role to a user."""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        old_custom_role = user.role.slug if user.role else None
        
        role_id = request.POST.get('role_id')
        if not role_id:
            roles = CustomRole.objects.filter(is_active=True)
            return render(request, 'accounts/assign_role.html', {
                'user': user,
                'roles': roles,
                'error': 'Please select a role'
            })
        
        role = get_object_or_404(CustomRole, id=role_id)
        user.role = role
        user.save()
        
        # Clear permission cache since role changed
        user.clear_permission_cache()
        
        # Log role change
        AuditLog.log(
            action=AuditLog.Action.ROLE_CHANGED,
            user=request.user,
            object_type='User',
            object_id=user.id,
            object_name=user.username,
            old_values={'role': old_custom_role},
            new_values={'role': user.role.slug},
            description=f"Changed {user.username}'s role to {user.role.name}",
            request=request
        )
        
        return redirect('user_list')
    
    roles = CustomRole.objects.filter(is_active=True)
    context = {
        'user': user,
        'roles': roles,
    }
    
    return render(request, 'accounts/assign_role.html', context)
