from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from django.db import IntegrityError
from django.contrib.auth.models import User


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                # Save the user to the database
                form.save()
                messages.success(request, "Registration successful! Please log in.")
                return redirect("login")
            except IntegrityError:
                messages.error(
                    request, "A user with this email already exists. Please try again."
                )
        else:
            messages.error(
                request, "Registration failed. Please correct the errors or use a different email address."
            )
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
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")
