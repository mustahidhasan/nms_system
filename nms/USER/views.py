from datetime import timezone
import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.http import JsonResponse
from nms.settings import EMAIL_HOST_USER
from .models import CustomUser, UserActivity
from django.contrib.sessions.models import Session
from django.utils import timezone
from .forms import RegisterForm, LoginForm

active_users = set()

from django.utils import timezone

import requests
from django.shortcuts import redirect
from django.conf import settings
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
        # Save token to session, or use it to call Graph API
        request.session['access_token'] = token_data['access_token']
        return redirect("ping_operation")  # or wherever you need to go
    else:
        return JsonResponse({'error': token_data}, status=400)


