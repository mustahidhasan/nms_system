# DASHBOARD/models.py

from django.conf import settings
from django.db import models

class GettingStartedA(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    input_one_1 = models.CharField(max_length=255)
    input_two_1 = models.CharField(max_length=255)
    input_one_2 = models.CharField(max_length=255)
    input_two_2 = models.CharField(max_length=255)
    input_one_3 = models.CharField(max_length=255)
    input_two_3 = models.CharField(max_length=255)
    input_one_4 = models.CharField(max_length=255)
    input_two_4 = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GettingStarted by {self.user}"
