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

def login_view(request):
    
    return redirect("ping_operation")  # Redirect to a dashboard or homepage


