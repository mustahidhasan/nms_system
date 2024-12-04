# dashboard/urls.py

from django.urls import path
from .views import logout_view, ping_operation, snmp_results

urlpatterns = [
    path("logout/", logout_view, name="logout"),
    path("", ping_operation, name="ping_operation"),
    path("snmp_results/", snmp_results, name="snmp_results"),
]
