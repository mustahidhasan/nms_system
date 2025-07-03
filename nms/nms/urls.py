from django.urls import path, include

urlpatterns = [
    # Your other urls ...
    path('', include('USER.urls')),  # or prefix with 'api/' if you prefer
]
