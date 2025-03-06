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

def generate_otp():
    return str(random.randint(100000, 999999))

def confirm_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        session_otp = request.session.get('otp')
        if entered_otp == session_otp:
            # OTP is correct, activate the user
            user_id = request.session.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True  # Activate the user account
            user.save()

            # Clear session OTP data
            del request.session['otp']
            del request.session['user_id']
            messages.success(request, "User registered successfully.")
            return redirect('login')
        else:
            messages.error(request, "OTP did not match.")
            return render(request, 'otp_verification.html')

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            otp = generate_otp()
            email = form.cleaned_data['email']
            
            try:
                user = form.save(commit=False)
                user.is_active = False  # Deactivate until OTP is confirmed
                user.save()

                # Store OTP and user ID in the session
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                
                # Send OTP email
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )

                messages.info(request, "An OTP has been sent to your email. Please enter it to complete registration.")
                return render(request, "otp_verification.html", {"email": email})

            except IntegrityError:
                messages.error(request, "A user with this email already exists.")
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

from django.utils import timezone

def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)

                # Record login activity with session start time
                UserActivity.objects.create(
                    user=user,
                    activity_type="Login",
                    session_start_time=timezone.now(),
                )

                # Store the user ID in the session
                request.session['user_id'] = user.id  # Store user ID in the session
                messages.success(request, "You are now logged in successfully.")
                return redirect("ping_operation")  # Redirect to a dashboard or homepage
            else:
                messages.error(request, "Invalid email or password. Please try again.")
        else:
            messages.error(request, "Login failed. Please check your inputs.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


from django.utils import timezone

@login_required
def logout_view(request):
    # Get the user activity related to the current session
    user_activity = UserActivity.objects.filter(user=request.user, activity_type="Login").last()
    print("line 118", user_activity)
    if user_activity:
        # Record the logout activity with session end time and duration
        user_activity.activity_type = "Logout"
        user_activity.session_end_time = timezone.now()
        user_activity.session_duration = user_activity.session_end_time - user_activity.session_start_time
        user_activity.save()

    # Remove the user from the active users set
    active_users.discard(request.user.id)
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


def get_active_users_count():
    # Retrieve all active sessions (not expired)
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    active_user_ids = []

    for session in active_sessions:
        session_data = session.get_decoded()  # Decode the session data
        user_id = session_data.get('_auth_user_id')
        if user_id:
            active_user_ids.append(user_id)

    # Retrieve all the users that are in the active sessions
    active_users = CustomUser.objects.filter(id__in=active_user_ids)
    return active_users

from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import CustomUser, UserActivity  # Import your models

def active_users_dashboard(request):
    # Retrieve the active user sessions
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    active_users = []

    for session in active_sessions:
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                active_users.append({
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                })
            except CustomUser.DoesNotExist:
                pass

    # Retrieve all user activities (login/logout)
    user_activities = UserActivity.objects.all().order_by('-timestamp')  # Order by latest activity
    
    active_user_count = len(active_users)  # Count the number of active users
    
    return render(request, "active_users_dashboard.html", {
        "active_user_count": active_user_count,
        "active_users": active_users,
        "user_activities": user_activities  # Pass activities to the template
    })
