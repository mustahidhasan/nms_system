from django.contrib import admin
from .models import GettingStartedA, SNMPWalk

class GettingStartedAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'appliance_action',  # Added field for appliance action
        'subnet_name',       # Added field for subnet name
        'start_ip_address',  # Added field for start IP address
        'end_ip_address',    # Added field for end IP address
        'email_server',      # Added field for email server
        'email_username',    # Added field for email username
        'email_password',    # Added field for email password
        'connection_security', # Added field for connection security
        'email_port',        # Added field for email port
        'selected_user',     # Added field for selected NMS Admin
        'created_at',        # Keep this to show the creation time
    ]
    
    # Exclude created_at from the add form
    exclude = ('created_at',)  # Keep this line to exclude created_at from the add form

admin.site.register(GettingStartedA, GettingStartedAdmin)

class SNMPWalkAdmin(admin.ModelAdmin):
    list_display = (
        'ip_address', 
        'snmp_port', 
        'snmp_version', 
        'snmp_command', 
        'oid', 
        'output_format', 
        'source_peer',
        "created_at",
    )
    search_fields = ('ip_address', 'oid', 'username', 'snmp_command')
    list_filter = ('snmp_version', 'snmp_command', 'output_format')

admin.site.register(SNMPWalk, SNMPWalkAdmin)