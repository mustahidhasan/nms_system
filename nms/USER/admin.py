from django.contrib import admin
from .models import UserActivity

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'activity_type', 'timestamp']  # Adjust based on your model fields
    search_fields = ['user__username', 'activity_type']          # Optional: improve admin search
    list_filter = ['activity_type', 'timestamp']                 # Optional: filter sidebar

# Alternatively, if you don't need customization:
# admin.site.register(UserActivity)
