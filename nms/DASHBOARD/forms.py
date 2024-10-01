from django import forms

class SNMPWalkForm(forms.Form):
    IP_ADDRESS_CHOICES = [
        ('127.0.0.1', 'Localhost'),
        # Add more options as needed
    ]
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
    
    ip_address = forms.CharField(label='IP Address/Hostname', max_length=100, required=True)
    snmp_port = forms.IntegerField(label='SNMP Port', initial=161, required=True)
    snmp_version = forms.ChoiceField(label='SNMP Version', choices=SNMP_VERSION_CHOICES, required=True)
    read_community_string = forms.CharField(label='Read Community String', max_length=100, required=False)
    username = forms.CharField(label='Username', max_length=100, required=False)
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput, required=False)
    authentication_type = forms.ChoiceField(label='Authentication Type', choices=AUTHENTICATION_TYPE_CHOICES, required=False)
    encryption_type = forms.ChoiceField(label='Encryption Type', choices=ENCRYPTION_TYPE_CHOICES, required=False)
    encryption_key = forms.CharField(label='Encryption Key', max_length=100, required=False)
    context_name = forms.CharField(label='Context Name', max_length=100, required=False)
    snmp_command = forms.ChoiceField(label='SNMP Command', choices=SNMP_COMMAND_CHOICES, required=True)
    oid = forms.CharField(label='OID', max_length=100, required=True,)
    output_format = forms.ChoiceField(label='Output Format', choices=OUTPUT_FORMAT_CHOICES, required=True)
    source_peer = forms.CharField(label='Source Peer', max_length=100, required=True)

