from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_queue_entry, name="create_queue_entry"),
    path("list/", views.queue_list, name="queue_list"),
    path("update/<int:entry_id>/", views.update_queue_entry, name="update_queue_entry"),

    # NEW: human-friendly dashboard
    path("dashboard/", views.queue_dashboard, name="queue_dashboard"),
]
