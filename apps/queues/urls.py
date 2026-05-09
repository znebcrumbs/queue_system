from django.urls import path
from . import views

urlpatterns = [
    path("departments/", views.department_selection, name="department_selection"),
    path("dashboard/", views.dashboard_v4, name="dashboard_v4"),
    path("kiosk/", views.kiosk_v4, name="kiosk_v4"),
    path("create/", views.create_queue_entry, name="create_queue_entry"),
    path("create-public/", views.create_queue_entry_public, name="create_queue_entry_public"),
    path("list/", views.queue_list, name="queue_list"),
    path("current-served/", views.get_current_served, name="get_current_served"),
    path("update/<int:entry_id>/", views.update_queue_entry, name="update_queue_entry"),
    path("ticket/<int:entry_id>/", views.queue_ticket, name="queue_ticket"),
    path("qr/<int:entry_id>/", views.generate_qr, name="generate_qr"),
    path("reports/", views.reports_dashboard, name="reports_dashboard"),
    path("reports/queues.csv", views.export_queues_csv, name="export_queues_csv"),
    path("reports/surveys.csv", views.export_surveys_csv, name="export_surveys_csv"),
    
    # Phase 4 Dashboard API Endpoints
    path("api/dashboard/kpi/", views.api_dashboard_kpi, name="api_dashboard_kpi"),
    path("api/dashboard/charts/", views.api_dashboard_charts, name="api_dashboard_charts"),
    path("api/dashboard/queue/", views.api_dashboard_queue, name="api_dashboard_queue"),
    
    # Phase 4 Admin Analytics API Endpoints
    path("api/admin/analytics/kpi/", views.api_admin_analytics_kpi, name="api_admin_analytics_kpi"),
    path("api/admin/analytics/charts/", views.api_admin_analytics_charts, name="api_admin_analytics_charts"),
    path("api/admin/analytics/tables/", views.api_admin_analytics_tables, name="api_admin_analytics_tables"),
    path("api/admin/analytics/audit/", views.api_admin_analytics_audit, name="api_admin_analytics_audit"),
    
    # Helper API Endpoints
    path("api/services/", views.api_get_services, name="api_get_services"),
]
