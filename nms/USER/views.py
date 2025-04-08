import requests
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse


def login_view(request):
    token_url = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"

    data = {
        'client_id': settings.AZURE_CLIENT_ID,
        'client_secret': settings.AZURE_CLIENT_SECRET,
        'grant_type': 'client_credentials',
        'scope': 'https://graph.microsoft.com/.default'
    }

    response = requests.post(token_url, data=data)
    token_data = response.json()

    if 'access_token' in token_data:
        request.session['access_token'] = token_data['access_token']
        return redirect("ping_operation")  # or wherever you want
    else:
        return JsonResponse({'error': token_data}, status=400)
