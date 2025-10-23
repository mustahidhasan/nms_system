import urllib.parse
import requests
from django.conf import settings
from django.contrib.auth import login, logout, get_user_model
from django.http import JsonResponse
from django.utils.timezone import now, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from USER.models import UserActivity
import urllib.parse
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.utils.timezone import now
from USER.models import User
from DASHBOARD.models import UserActivity
User = get_user_model()


def login_view(request):
    return JsonResponse({"message": "Render login page here (SSO button logic handled in frontend)"})




def azure_login(request):
    """
    Return JSON with Azure login URL for frontend to redirect user.
    """
    next_url = request.GET.get('next', '/dashboard')
    params = {
        'client_id': settings.AZURE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.AZURE_REDIRECT_URI,
        'response_mode': 'query',
        'scope': settings.AZURE_SCOPES,
        'state': urllib.parse.quote(next_url),  # Keep track of intended redirect
    }
    login_url = f"{settings.AZURE_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return JsonResponse({"login_url": login_url})


def azure_callback(request):
    """
    Handle Azure callback, exchange code for token, login user, redirect to frontend.
    """
    code = request.GET.get('code')
    next_url = urllib.parse.unquote(request.GET.get('state', '/dashboard'))

    if not code:
        return redirect(f"{settings.FRONTEND_URL}{next_url}")

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
            return JsonResponse({'error': 'Could not retrieve user email'}, status=400)

        user, created = User.objects.get_or_create(
            email=email, defaults={'username': email, 'first_name': name}
        )
        login(request, user)

        # Record login activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            timestamp=now(),
            session_status=True,
        )

        # Always redirect to frontend dashboard
        safe_redirect = next_url if next_url.startswith('/') else '/dashboard'
        return redirect(f"{settings.FRONTEND_URL}{safe_redirect}")

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def azure_logout(request):
    """
    Log out user and redirect to Azure logout page with frontend redirect.
    """
    user = request.user

    try:
        last_login_activity = UserActivity.objects.filter(
            user=user,
            activity_type='login',
            session_status=True
        ).latest('timestamp')

        duration_seconds = (now() - last_login_activity.timestamp).total_seconds()
        last_login_activity.session_status = False
        last_login_activity.duration = duration_seconds
        last_login_activity.save()

        UserActivity.objects.create(
            user=user,
            activity_type='logout',
            timestamp=now(),
            duration=0
        )
    except UserActivity.DoesNotExist:
        pass

    logout(request)

    azure_logout_url = (
        f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={settings.POST_LOGOUT_REDIRECT_URI}"
    )
    return JsonResponse({"logout_url": azure_logout_url})

@login_required
def active_users_dashboard(request):
    recent_threshold = now() - timedelta(minutes=15)
    recent_activities = UserActivity.objects.filter(timestamp__gte=recent_threshold)
    active_users = User.objects.filter(
        id__in=recent_activities.values_list('user_id', flat=True)
    ).distinct()

    user_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:100]

    return JsonResponse({
        "active_user_count": active_users.count(),
        "active_users": [
            {"id": user.id, "email": user.email, "name": user.first_name}
            for user in active_users
        ],
        "user_activities": [
            {
                "user_id": activity.user.id,
                "email": activity.user.email,
                "activity_type": activity.activity_type,
                "timestamp": activity.timestamp.isoformat(),
                "duration": activity.duration,
                "session_status": activity.session_status
            } for activity in user_activities
        ]
    })
