# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta

User = get_user_model()

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_status = models.BooleanField(default=True)
    duration = models.FloatField(null=True, blank=True)

    @property
    def formatted_duration(self):
        if self.duration:
            td = timedelta(seconds=self.duration)
            return str(td)
        return "N/A"

    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"
