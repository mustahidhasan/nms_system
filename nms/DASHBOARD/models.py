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

from django.db import models

class SNMPWalk(models.Model):
    SNMP_VERSION_CHOICES = [
        ('1', 'SNMPv1'),
        ('2c', 'SNMPv2c'),
        ('3', 'SNMPv3'),
    ]

    AUTHENTICATION_TYPE_CHOICES = [
        ('None', 'None'),
        ('MD5', 'MD5'),
        ('SHA', 'SHA'),
    ]

    ENCRYPTION_TYPE_CHOICES = [
        ('None', 'None'),
        ('AES', 'AES'),
        ('DES', 'DES'),
    ]

    SNMP_COMMAND_CHOICES = [
        ('snmpwalk', 'SNMP Walk'),
        ('snmpget', 'SNMP Get'),
    ]

    OUTPUT_FORMAT_CHOICES = [
        ('default', 'Default'),
        ('numeric', 'Numeric OIDs'),
        ('certification', 'Certification Walk'),
        ('hex', 'Hex String'),
    ]

    ip_address = models.CharField(max_length=100)
    snmp_port = models.IntegerField(default=161)
    snmp_version = models.CharField(max_length=3, choices=SNMP_VERSION_CHOICES)
    read_community_string = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    authentication_type = models.CharField(max_length=10, choices=AUTHENTICATION_TYPE_CHOICES, blank=True, null=True)
    encryption_type = models.CharField(max_length=10, choices=ENCRYPTION_TYPE_CHOICES, blank=True, null=True)
    encryption_key = models.CharField(max_length=100, blank=True, null=True)
    context_name = models.CharField(max_length=100, blank=True, null=True)
    snmp_command = models.CharField(max_length=10, choices=SNMP_COMMAND_CHOICES)
    oid = models.CharField(max_length=100)
    output_format = models.CharField(max_length=15, choices=OUTPUT_FORMAT_CHOICES)
    source_peer = models.CharField(max_length=100)

    def __str__(self):
        return f"SNMP Walk for {self.ip_address} - {self.snmp_command}"
