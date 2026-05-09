
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .decorators import require_permission

User = get_user_model()

@require_permission('manage_users')
def user_list(request):
    """List all users - requires manage_users permission."""
    users = User.objects.all().values("id", "username", "email", "custom_role__name")
    return JsonResponse(list(users), safe=False)



class CentralLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return "/admin/"  
        else:
            return "/queues/dashboard/"  
