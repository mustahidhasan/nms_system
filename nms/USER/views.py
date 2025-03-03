from datetime import timezone
import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.http import JsonResponse
from nms.settings import EMAIL_HOST_USER
from .models import CustomUser 

from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.sessions.models import Session
from django.utils import timezone

active_users = set()

def confirm_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        session_otp = request.session.get('otp')
        print("line 17", entered_otp,  session_otp)
        if entered_otp == session_otp:
            # OTP is correct, activate the user
            user_id = request.session.get('user_id')
            user = CustomUser.objects.get(id=user_id)
            user.is_active = True  # Activate the user account
            user.save()

            # Clear session OTP data
            del request.session['otp']
            del request.session['user_id']
            messages.success(request, "user registered successfully")
            return redirect('login')
        else:
            messages.success(request, "OTP did not matched")
            return render(request, 'otp_verification.html')

def generate_otp():
    return str(random.randint(100000, 999999))

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Generate OTP and send it to the user's email
            otp = generate_otp()
            email = form.cleaned_data['email']
            
            try:
                # Save the form data temporarily but don't commit yet
                user = form.save(commit=False)
                user.is_active = False  # Deactivate the account until OTP is confirmed
                user.save()

                # Store the OTP in the session to verify later
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                print("line 52", EMAIL_HOST_USER, otp)
                # Send OTP to user's email
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    EMAIL_HOST_USER,  # Replace with your domain email
                    [email],
                    fail_silently=False,
                )

                messages.info(request, "An OTP has been sent to your email. Please enter it to complete registration.")

                return render(request, "otp_verification.html", {"email": email})

            except IntegrityError:
                messages.error(request, "A user with this email already exists. Please try again.")
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})




def login_view(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)

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


@login_required
def logout_view(request):
    # Remove the user from the active users set
    active_users.discard(request.user.id)
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import CustomUser  # Import your custom user model

def get_active_users_count():
    # Retrieve all active sessions (not expired)
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())  # Only non-expired sessions
    active_users = []

    for session in active_sessions:
        session_data = session.get_decoded()  # Decode the session data
        user_id = session_data.get('_auth_user_id')  # Get the stored user ID in session
        if user_id:
            # Get the custom user object from the database using the user_id
            try:
                user = CustomUser.objects.get(id=user_id)
                active_users.append({
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                })
            except CustomUser.DoesNotExist:
                # Handle the case if the user is not found (although rare)
                pass

    return active_users



@login_required
def active_users_dashboard(request):
    active_users = get_active_users_count()  # Retrieve the active users details
    active_user_count = len(active_users)  # Count the number of active users
    print("line 138", active_user_count)
    return render(request, "active_users_dashboard.html", {
        "active_user_count": active_user_count,
        "active_users": active_users,
    })
