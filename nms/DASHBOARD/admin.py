# DASHBOARD/admin.py

from django.contrib import admin
from .models import GettingStartedA

class GettingStartedAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'input_one_1',
        'input_two_1',
        'input_one_2',
        'input_two_2',
        'input_one_3',
        'input_two_3',
        'input_one_4',
        'input_two_4',
        'created_at',  # You can keep this in list_display to show it in the change list
    ]
    # Exclude created_at from the add form
    exclude = ('created_at',)  # Add this line

admin.site.register(GettingStartedA, GettingStartedAdmin)
