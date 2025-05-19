import urllib.parse
import requests
from django.conf import settings
from django.shortcuts import redirect, render
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()
def login_view(request):
    """
    Renders the login page with the 'Login via SSO' button.
    """
    return render(request, 'login.html')

def azure_login(request):
    """
    Initiates the Microsoft Azure login by redirecting the user
    to the Microsoft authorization endpoint.
    """
    params = {
        'client_id': settings.AZURE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.AZURE_REDIRECT_URI,
        'response_mode': 'query',
        'scope': settings.AZURE_SCOPES,
        'state': 'some_random_state',  # Optional but recommended for CSRF
    }

    login_url = f"{settings.AZURE_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return redirect(login_url)


def azure_callback(request):
    """
    Handles the callback from Azure after successful login.
    Exchanges the authorization code for an access token,
    fetches user info from Microsoft Graph, and logs the user into Django.
    """
    code = request.GET.get('code')

    # Exchange authorization code for access token
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

        # Get user info from Microsoft Graph
        headers = {'Authorization': f"Bearer {tokens['access_token']}"}
        graph_response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        user_info = graph_response.json()

        email = user_info.get('mail') or user_info.get('userPrincipalName')
        name = user_info.get('displayName') or email

        if not email:
            return JsonResponse({'error': 'Could not retrieve user email from Microsoft Graph'}, status=400)

        # Create or get user in Django
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'first_name': name}
        )

        # Log the user in
        login(request, user)
        # Record login activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            timestamp=now(),
            session_status=True,
        )
        return redirect('ping_operation')  # Replace with your post-login view

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
from django.contrib.auth import logout

from USER.models import UserActivity

def azure_logout(request):
    user = request.user

    # Find the most recent login session for this user
    try:
        last_login_activity = UserActivity.objects.filter(
            user=user,
            activity_type='login',
            session_status=True
        ).latest('timestamp')

        # Calculate duration
        duration_seconds = (now() - last_login_activity.timestamp).total_seconds()

        # Update the login activity to mark session closed and duration
        last_login_activity.session_status = False
        last_login_activity.duration = duration_seconds
        last_login_activity.save()

        # Record logout activity (optional)
        UserActivity.objects.create(
            user=user,
            activity_type='logout',
            timestamp=now(),
            duration=0
        )
    except UserActivity.DoesNotExist:
        pass  # No login activity found, skip tracking

    logout(request)  # Django logout

    azure_logout_url = (
        f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={settings.POST_LOGOUT_REDIRECT_URI}"
    )
    return redirect(azure_logout_url)

from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, timedelta
from django.shortcuts import render
from USER.models import UserActivity
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def active_users_dashboard(request):
    """
    Shows the dashboard of currently active users and their activity logs.
    """

    # Users active in the last 15 minutes
    recent_threshold = now() - timedelta(minutes=15)
    recent_activities = UserActivity.objects.filter(timestamp__gte=recent_threshold)
    active_users = User.objects.filter(id__in=recent_activities.values_list('user_id', flat=True)).distinct()

    # Recent activity logs (latest 100 for performance, can be adjusted)
    user_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:100]

    context = {
        'active_users': active_users,
        'active_user_count': active_users.count(),
        'user_activities': user_activities,
    }

    return render(request, 'active_users_dashboard.html', context)
