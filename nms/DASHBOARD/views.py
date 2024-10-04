# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from .forms import SNMPWalkForm
from .models import SNMPWalk
import subprocess
# Import necessary modules from pysnmp
from pysnmp.hlapi import (
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    nextCmd,
    UsmUserData,
    usmNoAuthProtocol,
    usmNoPrivProtocol,
    usmHMACMD5AuthProtocol,
    usmHMACSHAAuthProtocol,
    usmAesCfb128Protocol,
    usmDESPrivProtocol,
)

    

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")  # Replace 'login' with the name of your login URL


def ping_operation(request):
    ping_result = None
    error_message = None

    if request.method == 'POST':
        ip_address = request.POST.get('ip_address')
        try:
            # Use subprocess to run the ping command
            ping_output = subprocess.run(
                ['ping', '-c', '4', ip_address],  # Run 'ping' command with 4 packets
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if ping_output.returncode == 0:
                ping_result = ping_output.stdout  # Capture the ping output
            else:
                error_message = f"Ping failed: {ping_output.stderr}"
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"

    return render(request, 'dashboard.html', {'ping_result': ping_result, 'error_message': error_message})

@login_required
def dashboard_view(request):
    if request.method == 'POST':
        form = SNMPWalkForm(request.POST)
        if form.is_valid():
            ip_address = form.cleaned_data['ip_address']
            snmp_port = form.cleaned_data['snmp_port']
            snmp_version = form.cleaned_data['snmp_version']
            read_community_string = form.cleaned_data.get('read_community_string', 'public')
            username = form.cleaned_data.get('username', '')
            password = form.cleaned_data.get('password', '')
            authentication_type = form.cleaned_data.get('authentication_type', '')
            encryption_type = form.cleaned_data.get('encryption_type', '')
            encryption_key = form.cleaned_data.get('encryption_key', '')
            context_name = form.cleaned_data.get('context_name', '')
            snmp_command = form.cleaned_data['snmp_command']
            oid = form.cleaned_data['oid']
            output_format = form.cleaned_data['output_format']
            source_peer = form.cleaned_data['source_peer']
            
            # SNMP Version Handling
            if snmp_version in ['1', '2c']:
                # Use SNMP v1 or v2c
                result = []
                for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                    SnmpEngine(),
                    CommunityData(read_community_string, mpModel=0 if snmp_version == '1' else 1),
                    UdpTransportTarget((ip_address, snmp_port)),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=False
                ):
                    if errorIndication:
                        result.append(f'Error: {errorIndication}')
                        break
                    elif errorStatus:
                        result.append(f'Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}')
                        break
                    else:
                        for varBind in varBinds:
                            result.append(f'{varBind[0]} = {varBind[1]}')

            elif snmp_version == '3':
                # Use SNMP v3 with optional authentication and encryption
                auth_protocol = usmNoAuthProtocol
                priv_protocol = usmNoPrivProtocol

                if authentication_type == 'MD5':
                    auth_protocol = usmHMACMD5AuthProtocol
                elif authentication_type == 'SHA':
                    auth_protocol = usmHMACSHAAuthProtocol

                if encryption_type == 'AES':
                    priv_protocol = usmAesCfb128Protocol
                elif encryption_type == 'DES':
                    priv_protocol = usmDESPrivProtocol

                result = []
                for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                    SnmpEngine(),
                    UsmUserData(username, password, encryption_key, authProtocol=auth_protocol, privProtocol=priv_protocol),
                    UdpTransportTarget((ip_address, snmp_port)),
                    ContextData(context_name),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=False
                ):
                    if errorIndication:
                        result.append(f'Error: {errorIndication}')
                        break
                    elif errorStatus:
                        result.append(f'Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}')
                        break
                    else:
                        for varBind in varBinds:
                            result.append(f'{varBind[0]} = {varBind[1]}')
            snmp_walk = SNMPWalk(
                ip_address=form.cleaned_data['ip_address'],
                snmp_port=form.cleaned_data['snmp_port'],
                snmp_version=form.cleaned_data['snmp_version'],
                read_community_string=form.cleaned_data.get('read_community_string', ''),
                username=form.cleaned_data.get('username', ''),
                password=form.cleaned_data.get('password', ''),
                authentication_type=form.cleaned_data.get('authentication_type', ''),
                encryption_type=form.cleaned_data.get('encryption_type', ''),
                encryption_key=form.cleaned_data.get('encryption_key', ''),
                context_name=form.cleaned_data.get('context_name', ''),
                snmp_command=form.cleaned_data['snmp_command'],
                oid=form.cleaned_data['oid'],
                output_format=form.cleaned_data['output_format'],
                source_peer=form.cleaned_data['source_peer'],
                result=result
            )
            snmp_walk.save()
            # Render results in the result page
            all_data = SNMPWalk.objects.last()
            return render(request, 'dashboard.html', {'form': form, 'result':all_data})
    else:
        form = SNMPWalkForm()

    return render(request, 'dashboard.html', {'form': form})
