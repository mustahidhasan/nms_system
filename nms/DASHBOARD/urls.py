# dashboard/urls.py

from django.urls import path
from .views import dashboard_view, logout_view, ping_operation

urlpatterns = [
    path('', dashboard_view, name='dashboard'),  # Assuming this is the root URL for the dashboard
    path('logout/', logout_view, name='logout'),
    path('ping/', ping_operation, name='ping_operation'),
   
    
]
