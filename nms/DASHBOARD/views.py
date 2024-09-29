# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect


@login_required
def dashboard_view(request):
    # Check if the user is a superuser and if they haven't disabled the modal for this session
    if request.user.is_superuser and not request.session.get("dont_show_modal", False):
        return render(request, "dashboard.html", {"is_superuser": True})
    return render(request, "dashboard.html", {"is_superuser": False})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")  # Replace 'login' with the name of your login URL


@login_required
def welcome_superuser(request):
    if request.user.is_superuser:
        return render(
            request, "welcome_superuser.html"
        )  # Replace with your welcome template
    else:
        return redirect(
            "dashboard"
        )  # Redirect non-superusers to the dashboard or another page


@login_required
def disable_modal(request):
    # This view will set the session to not show the modal again
    request.session["dont_show_modal"] = True
    return redirect("dashboard")
