# dashboard/urls.py

from django.urls import path
from .views import dashboard_view, logout_view, welcome_superuser, disable_modal

urlpatterns = [
    path('', dashboard_view, name='dashboard'),  # Assuming this is the root URL for the dashboard
    path('logout/', logout_view, name='logout'),
    path('welcome/', welcome_superuser, name='welcome_superuser'),
    path('disable-modal/', disable_modal, name='disable_modal'),
    
]
