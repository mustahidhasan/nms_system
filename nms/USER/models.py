from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.timezone import now
from django.conf import settings  # Get the custom user model dynamically

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = None  # Remove the default username field

    USERNAME_FIELD = "email"  # Use email as the username field
    REQUIRED_FIELDS = ["first_name", "last_name"]  # Fields required in createsuperuser

    objects = CustomUserManager()

    def __str__(self):
        return self.email


from django.db import models
from django.contrib.auth import get_user_model

class UserActivity(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)  # e.g., "Login" or "Logout"
    timestamp = models.DateTimeField(auto_now_add=True)
    session_start_time = models.DateTimeField(null=True, blank=True)
    session_end_time = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)  # Store duration
    session_status = models.BooleanField(null=True, blank=True, default=False)

    def __str__(self):
        return f'{self.user} - {self.activity_type} - {self.timestamp}'

