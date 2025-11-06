from django.contrib import admin
from django.urls import include, path

# Reuse the same app routes under an /api prefix so local dev can hit /api/*
# just like production behind Nginx.
api_patterns = [
    path("", include("USER.urls")),
    path("dashboard/", include("DASHBOARD.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("USER.urls")),
    path("dashboard/", include("DASHBOARD.urls")),
    path("api/", include(api_patterns)),
]
