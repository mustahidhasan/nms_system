# main_app/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Starts session
            return redirect("ping_operation")  # Redirect to the dashboard
    else:
        form = RegisterForm()
    return render(request, "", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the "next" URL if available, otherwise to the dashboard
            next_url = request.GET.get("next", "ping_operation")
            return redirect(next_url)
    return render(request, "login.html")
