# main_app/urls.py (or wherever your main app's URLs are defined)

from django.urls import path, include
from .views import register_view, login_view, confirm_otp
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("register/", register_view, name="register"),
    path('verify-otp/', confirm_otp, name='confirm_otp'),
    path("", login_view, name="login"),
    path("dashboard/", include("DASHBOARD.urls")),  # Include the dashboard app URLs
    path(
        "password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
