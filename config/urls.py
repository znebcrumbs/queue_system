"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from apps.queues import views as queue_views
from apps.accounts.views import CentralLoginView
from apps.queues import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("queues/", include("apps.queues.urls")),
    path("survey/", include("apps.survey.urls")),
    path("audit/", include("apps.audit.urls")),
    path("login/", CentralLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    path('', views.kiosk_v4, name='kiosk'),
    path("admin/reports/", views.admin_reports_dashboard, name="admin_reports_dashboard"),
    path("admin/v4/analytics/", views.admin_analytics, name="admin_analytics"),


    # Authentication
   # path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
   # path("logout/", auth_views.LogoutView.as_view(next_page="landing"), name="logout"),

]
