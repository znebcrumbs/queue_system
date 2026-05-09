"""Views for audit log reports and analytics."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog


@login_required
def audit_log_list(request):
    """Display audit logs with filtering."""
    logs = AuditLog.objects.all().order_by('-timestamp')[:1000]
    
    # Filters
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    context = {
        'logs': logs,
        'action_choices': AuditLog.Action.choices,
    }
    return render(request, 'audit/audit_log_list.html', context)


@login_required
def audit_log_stats(request):
    """Display audit log statistics."""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    stats = {
        'total_logs': AuditLog.objects.count(),
        'logs_24h': AuditLog.objects.filter(timestamp__gte=last_24h).count(),
        'logs_7d': AuditLog.objects.filter(timestamp__gte=last_7d).count(),
        'logs_30d': AuditLog.objects.filter(timestamp__gte=last_30d).count(),
        'actions_24h': AuditLog.objects.filter(timestamp__gte=last_24h).values('action').annotate(count=Count('id')).order_by('-count'),
        'users': AuditLog.objects.filter(user__isnull=False).values('user__username').annotate(count=Count('id')).order_by('-count')[:10],
        'failed_logins_24h': AuditLog.objects.filter(
            timestamp__gte=last_24h,
            action=AuditLog.Action.FAILED_LOGIN
        ).count(),
        'unauthorized_24h': AuditLog.objects.filter(
            timestamp__gte=last_24h,
            action__in=[AuditLog.Action.UNAUTHORIZED_ACCESS, AuditLog.Action.PERMISSION_DENIED]
        ).count(),
    }
    
    context = {'stats': stats}
    return render(request, 'audit/audit_stats.html', context)
