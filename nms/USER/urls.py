# main_app/urls.py (or wherever your main app's URLs are defined)

from django.urls import path, include
from .views import login_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", login_view, name="login"),
    path("dashboard/", include("DASHBOARD.urls")),  # Include the dashboard app URLs
   

]
