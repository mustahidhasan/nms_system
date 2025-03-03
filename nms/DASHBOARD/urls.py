# dashboard/urls.py

from django.urls import path
from .views import logout_view, ping_operation, snmp_results, send_email

urlpatterns = [
    path("logout/", logout_view, name="logout"),
    path("", ping_operation, name="ping_operation"),
    path('send-email/', send_email, name='send_email'),
]
