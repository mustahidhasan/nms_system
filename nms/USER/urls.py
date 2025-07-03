from django.urls import path
from . import views

urlpatterns = [
    path('api/auth/login_url/', views.get_azure_login_url, name='azure_login_url'),
    path('api/auth/callback/', views.azure_callback, name='azure_callback'),
    path('oauth2/callback/', views.azure_callback, name='azure_callback_alt'),  # Add this!
    path('api/auth/logout/', views.azure_logout, name='azure_logout'),
    path('api/active-users/', views.active_users_api, name='active_users_api'),
]

