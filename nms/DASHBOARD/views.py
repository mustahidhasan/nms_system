# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')  # Render the dashboard template

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')  # Replace 'login' with the name of your login URL
