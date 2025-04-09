# views.py
import urllib.parse
from django.conf import settings
from django.shortcuts import redirect


def azure_login(request):
    params = {
        'client_id': settings.AZURE_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': settings.AZURE_REDIRECT_URI,
        'response_mode': 'query',
        'scope': settings.AZURE_SCOPES,
        'state': 'some_random_state',  # optional for CSRF
    }

    login_url = f"{settings.AZURE_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return redirect(login_url)
# views.py
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse


def azure_callback(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'No code returned from Microsoft'}, status=400)

    token_data = {
        'client_id': settings.AZURE_CLIENT_ID,
        'scope': settings.AZURE_SCOPES,
        'code': code,
        'redirect_uri': settings.AZURE_REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': settings.AZURE_CLIENT_SECRET,
    }

    token_response = requests.post(settings.AZURE_TOKEN_ENDPOINT, data=token_data)
    tokens = token_response.json()

    if 'access_token' not in tokens:
        return JsonResponse({'error': tokens}, status=400)

    # Get user info from Graph API
    headers = {'Authorization': f"Bearer {tokens['access_token']}"}
    user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()

    email = user_info.get('mail') or user_info.get('userPrincipalName')
    name = user_info.get('displayName') or email

    user, created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': name}
    )

    login(request, user)  # Django login
    return redirect('ping_operation')  # Redirect to your secure view
