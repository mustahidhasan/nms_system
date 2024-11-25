# dashboard/urls.py

from django.urls import path
from .views import dns_view, add_dns

urlpatterns = [
    path('', dns_view, name='dns_view'),
    path('add_dns/', add_dns, name='add_dns'),
   
    
]
