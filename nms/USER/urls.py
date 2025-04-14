# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.azure_login, name='azure_login'),
    path('auth/callback/', views.azure_callback, name='azure_callback'),
]
