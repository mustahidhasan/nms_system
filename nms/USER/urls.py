# urls.py
from django.urls import path
from .views import azure_login, azure_callback

urlpatterns = [
    path("", azure_login, name="azure_login"),
    path("auth/callback/", azure_callback, name="azure_callback"),
]
