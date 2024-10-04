from django.contrib import admin
from .models import SNMPWalk

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