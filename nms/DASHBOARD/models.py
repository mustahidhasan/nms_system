from django.conf import settings
from django.db import models

class GettingStartedA(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Section 1: Appliance Action
    appliance_action = models.CharField(max_length=50)  # To store the chosen appliance action

    # Section 2: Scan Subnets
    subnet_name = models.CharField(max_length=255)  # To store the subnet name
    start_ip_address = models.GenericIPAddressField(protocol='IPv4')  # To store the start IP address
    end_ip_address = models.GenericIPAddressField(protocol='IPv4')  # To store the end IP address

    # Section 3: Email Server Details
    email_server = models.CharField(max_length=255)  # To store the email server
    email_username = models.CharField(max_length=255)  # To store the email username
    email_password = models.CharField(max_length=255)  # To store the email password
    connection_security = models.CharField(max_length=50)  # To store the connection security
    email_port = models.PositiveIntegerField()  # To store the email port

    # Section 4: Selected NMS Admin (user)
    selected_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='selected_users')  # To store the selected NMS Admin

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GettingStarted by {self.user.username}"
