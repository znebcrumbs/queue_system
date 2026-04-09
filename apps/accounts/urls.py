from django.urls import path
from apps.accounts.views import CentralLoginView
from . import views
from . import role_management_views

urlpatterns = [
    path("users/", views.user_list, name="user_list"),
    path("login/", CentralLoginView.as_view(), name="login"),
    
    # Role Management
    path("roles/", role_management_views.role_list, name="role_list"),
    path("roles/create/", role_management_views.role_create, name="role_create"),
    path("roles/<int:role_id>/", role_management_views.role_detail, name="role_detail"),
    path("roles/<int:role_id>/delete/", role_management_views.role_delete, name="role_delete"),
    
    # Permission Management
    path("permissions/", role_management_views.permission_list, name="permission_list"),
    path("permissions/create/", role_management_views.permission_create, name="permission_create"),
    path("permissions/<int:permission_id>/delete/", role_management_views.permission_delete, name="permission_delete"),
    
    # User Role Assignment
    path("users/<int:user_id>/assign-role/", role_management_views.assign_role, name="assign_role"),
]
