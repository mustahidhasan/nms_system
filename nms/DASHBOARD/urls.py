# dashboard/urls.py

from django.urls import path
from .views import dashboard_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),  # Assuming this is the root URL for the dashboard
]
