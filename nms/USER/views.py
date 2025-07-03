import urllib.parse
import requests
from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import F

from .models import UserActivity

User = get_user_model()

def get_azure_login_url(request):
    params = {
        'client_id': settings.AZURE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.AZURE_REDIRECT_URI,
        'response_mode': 'query',
        'scope': settings.AZURE_SCOPES,
        'state': 'xyz',
    }
    login_url = f"{settings.AZURE_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return JsonResponse({'login_url': login_url})

def azure_callback(request):
    code = request.GET.get('code')
    token_data = {
        'client_id': settings.AZURE_CLIENT_ID,
        'scope': settings.AZURE_SCOPES,
        'code': code,
        'redirect_uri': settings.AZURE_REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': settings.AZURE_CLIENT_SECRET,
    }

    try:
        token_response = requests.post(settings.AZURE_TOKEN_ENDPOINT, data=token_data)
        tokens = token_response.json()

        if 'access_token' not in tokens:
            return JsonResponse({'error': 'Token exchange failed', 'details': tokens}, status=400)

        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        graph_response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        user_info = graph_response.json()

        email = user_info.get('mail') or user_info.get('userPrincipalName')
        name = user_info.get('displayName') or email

        if not email:
            return JsonResponse({'error': 'Email not found from Azure'}, status=400)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email, 'first_name': name}
        )

        login(request, user)

        UserActivity.objects.create(
            user=user,
            activity_type='login',
            timestamp=now(),
            session_status=True,
        )

        return JsonResponse({'message': 'Login successful', 'user': {'email': user.email, 'first_name': user.first_name}})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def azure_logout(request):
    user = request.user
    try:
        last_login = UserActivity.objects.filter(user=user, activity_type='login', session_status=True).latest('timestamp')
        duration = (now() - last_login.timestamp).total_seconds()
        last_login.session_status = False
        last_login.duration = duration
        last_login.save()

        UserActivity.objects.create(user=user, activity_type='logout', timestamp=now(), duration=0)
    except UserActivity.DoesNotExist:
        pass

    logout(request)
    return JsonResponse({'message': 'Logout successful'})

@login_required
def active_users_api(request):
    threshold = now() - timedelta(minutes=15)
    recent_activities = UserActivity.objects.filter(timestamp__gte=threshold)
    active_user_ids = recent_activities.values_list('user_id', flat=True).distinct()
    active_users = list(User.objects.filter(id__in=active_user_ids).values('first_name', 'email', 'is_active'))

    logs = UserActivity.objects.select_related('user').order_by('-timestamp')[:100].values(
        user__id=F('user__id'),
        user__username=F('user__username'),
        timestamp=F('timestamp'),
        activity_type=F('activity_type'),
        duration=F('duration'),
    )

    return JsonResponse({
        'active_user_count': len(active_users),
        'active_users': active_users,
        'user_activities': list(logs),
    })
