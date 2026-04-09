
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def user_list(request):
    users = User.objects.all().values("id", "username", "email", "role")
    return JsonResponse(list(users), safe=False)



class CentralLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return "/admin/"  
        else:
            return "/queues/dashboard/"  
