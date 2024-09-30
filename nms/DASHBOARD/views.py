# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import GettingStartedA  # Import your model here
from django.urls import reverse
from USER.models import CustomUser
from django.contrib.auth.models import AbstractUser
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
        users = CustomUser.objects.all()  # Fetch all users
        return render(
            request, "welcome_superuser.html", {'users': users}  # Pass users to the template
        )
    else:
        return redirect("dashboard")  # Redirect non-superusers to the dashboard or another page



@login_required
def disable_modal(request):
    # This view will set the session to not show the modal again
    request.session["dont_show_modal"] = True
    return redirect("dashboard")


# Form submission view
@login_required
def submit_form(request):
    if request.method == 'POST':
        # Get form data from POST request
        input_one_1 = request.POST.get('input_one_1')
        input_two_1 = request.POST.get('input_two_1')
        input_one_2 = request.POST.get('input_one_2')
        input_two_2 = request.POST.get('input_two_2')
        input_one_3 = request.POST.get('input_one_3')
        input_two_3 = request.POST.get('input_two_3')
        input_one_4 = request.POST.get('input_one_4')
        input_two_4 = request.POST.get('input_two_4')

        # Save data to the GettingStartedA model
        GettingStartedA.objects.create(
            user=request.user,  # Assuming user is logged in
            input_one_1=input_one_1,
            input_two_1=input_two_1,
            input_one_2=input_one_2,
            input_two_2=input_two_2,
            input_one_3=input_one_3,
            input_two_3=input_two_3,
            input_one_4=input_one_4,
            input_two_4=input_two_4,
        )

        # Redirect after successful form submission
        return redirect(reverse('dashboard'))  # Replace 'dashboard' with your actual URL name

    else:
        # Render an empty form if the request method is GET
        return render(request, 'DASHBOARD/submit_form.html')
