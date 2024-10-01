# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import GettingStartedA  # Import your model here
from django.urls import reverse
from USER.models import CustomUser
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from .forms import SNMPWalkForm

@login_required
def dashboard_view(request):
    # Check if the user is a superuser and if they haven't disabled the modal for this session
    if request.user.is_superuser and not request.session.get("dont_show_modal", False):
        return render(request, "dashboard.html", {"is_superuser": True})
    return render(request, "dashboard.html", {"is_superuser": False})


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")  # Replace 'login' with the name of your login URL


@login_required
def welcome_superuser(request):
    if request.user.is_superuser:
        users = CustomUser.objects.all()  # Fetch all users
        return render(
            request, "welcome_superuser.html", {'users': users}  # Pass users to the template
        )
    else:
        return redirect("dashboard")  # Redirect non-superusers to the dashboard or another page



@login_required
def disable_modal(request):
    # This view will set the session to not show the modal again
    request.session["dont_show_modal"] = True
    return redirect("dashboard")


@login_required
def submit_form(request):
    if request.method == 'POST':
        # Get form data from POST request
        appliance_action = request.POST.get('appliance_action')  # Adjusted to match your input field names
        subnet_name = request.POST.get('subnet_name')
        start_ip_address = request.POST.get('start_ip_address')
        end_ip_address = request.POST.get('end_ip_address')
        email_server = request.POST.get('email_server')
        email_username = request.POST.get('email_username')
        email_password = request.POST.get('email_password')
        connection_security = request.POST.get('connection_security')
        email_port = request.POST.get('email_port')
        selected_user_id = request.POST.get('user')  # The id of the selected user

        # Save data to the GettingStartedA model
        GettingStartedA.objects.create(
            user=request.user,  # Assuming user is logged in
            appliance_action=appliance_action,
            subnet_name=subnet_name,
            start_ip_address=start_ip_address,
            end_ip_address=end_ip_address,
            email_server=email_server,
            email_username=email_username,
            email_password=email_password,
            connection_security=connection_security,
            email_port=email_port,
            selected_user_id=selected_user_id  # Use the selected user id
        )

        # Redirect after successful form submission
        return redirect(reverse('dashboard'))  # Replace 'dashboard' with your actual URL name

    else:
        # Render an empty form if the request method is GET
        return render(request, 'DASHBOARD/submit_form.html')




from django.shortcuts import render
from .forms import SNMPWalkForm

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

def snmp_walk(request):
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

            # Render results in the result page
            return render(request, 'DASHBOARD/snmp_walk.html', {'form': form, 'result': '\n'.join(result)})
    else:
        form = SNMPWalkForm()

    return render(request, 'DASHBOARD/snmp_walk.html', {'form': form})
