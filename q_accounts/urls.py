from django.urls import path
from q_accounts.views import CentralLoginView
from . import views

urlpatterns = [
    path("users/", views.user_list, name="user_list"),
    path("login/", CentralLoginView.as_view(), name="login"),
]
