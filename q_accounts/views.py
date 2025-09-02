from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def user_list(request):
    users = User.objects.all().values("id", "username", "email", "role")
    return JsonResponse(list(users), safe=False)
