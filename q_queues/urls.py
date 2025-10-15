from django.urls import path
from . import views

urlpatterns = [
     path("", views.department_selection, name="department_selection"),  # splash page
    path("kiosk/<int:department_id>/", views.kiosk, name="kiosk"),
    path("dashboard/", views.dashboard, name="dashboard"), #html
    path("create/", views.create_queue_entry, name="create_queue_entry"),
    path("list/", views.queue_list, name="queue_list"),
    path("update/<int:entry_id>/", views.update_queue_entry, name="update_queue_entry"),
    path("kiosk/", views.kiosk, name="kiosk"),
    path("ticket/<int:entry_id>/", views.queue_ticket, name="queue_ticket"), #html
    path("qr/<int:entry_id>/", views.generate_qr, name="generate_qr"),
    path("reports/", views.reports_dashboard, name="reports_dashboard"),
    path("reports/queues.csv", views.export_queues_csv, name="export_queues_csv"),
    path("reports/surveys.csv", views.export_surveys_csv, name="export_surveys_csv"),
]
