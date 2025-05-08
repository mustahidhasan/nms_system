from django.urls import path
from . import views

urlpatterns = [
    path('', views.azure_login, name='azure_login'),
    path('oauth2/callback/', views.azure_callback, name='azure_callback'),
]