# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
import subprocess
import platform
import logging
import socket

from DNS.models import DNS

logger = logging.getLogger(__name__)

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


@login_required
def ping_operation(request):
    if request.method == "POST":
        ip_address = request.POST.get("ip_address")
        enable_ping = request.POST.get("enable_ping")
        verbose_ping = request.POST.get("verbose_ping")
        traceroute = request.POST.get("traceroute")
        dns_lookup = request.POST.get("dns_lookup")
        snmp_walk = request.POST.get("snmp_walk")
        # Get all DNS names as a list
        dns_names = list(DNS.objects.values_list("dns_name", flat=True))

        # Check if IP address or domain name is provided
        if not ip_address:
            return render(
                request,
                "ping.html",
                {"error_message": "Please provide an IP address or domain name."},
            )

        # Detect the operating system
        os_name = platform.system()
        results = []

        try:
            # Perform Enable Ping
            if enable_ping:
                if os_name == "Windows":
                    command = ["ping", "-n", "1", ip_address]
                else:
                    command = ["ping", "-c", "1", ip_address]

                logger.info(f"Pinging {ip_address} with basic ping.")
                response = subprocess.run(command, capture_output=True, text=True)
                results.append(f"<b>Enable Ping:</b> {'Device is alive' if response.returncode == 0 else 'Device is unreachable'}<br>")

            # Perform Verbose Ping
            if verbose_ping:
                if os_name == "Windows":
                    command = ["ping", "-n", "4", ip_address]
                else:
                    command = ["ping", "-c", "4", ip_address]

                logger.info(f"Pinging {ip_address} with verbose ping.")
                response = subprocess.run(command, capture_output=True, text=True)
                results.append(
                    f"<b>Verbose Ping Result:</b><pre>{response.stdout}</pre>" if response.returncode == 0 else "<b>Verbose Ping failed.</b><br>"
                )

            # Perform Traceroute
            if traceroute:
                if os_name == "Windows":
                    command = ["tracert", ip_address]
                else:
                    command = ["traceroute", ip_address]

                logger.info(f"Running traceroute for {ip_address}.")
                response = subprocess.run(command, capture_output=True, text=True)
                results.append(
                    f"<b>Traceroute Result:</b><pre>{response.stdout}</pre>" if response.returncode == 0 else "<b>Traceroute failed.</b><br>"
                )

            # Perform DNS Lookup
            if dns_lookup:
                ip_address_d = socket.gethostbyname(ip_address)
                if ip_address_d in dns_names:
                    logger.info("IP address exists in DNS records.")
                    if os_name == "Windows":
                        command = ["nslookup", ip_address]
                    else:
                        command = ["dig", ip_address]
                    response = subprocess.run(command, capture_output=True, text=True)
                    if response.returncode == 0:
                        results.append(f"<b>DNS Lookup Result:</b><pre>{response.stdout}</pre>")
                    else:
                        results.append("<b>DNS Lookup failed.</b><br>")
                else:
                    results.append("<b>DNS Lookup Result:</b> DNS IP did not match the record.<br>")

            # Perform SNMP Walk
            if snmp_walk:
                snmp_port = request.POST.get("snmp_port", 161)
                snmp_version = request.POST.get("snmp_version")
                read_community_string = request.POST.get("read_community_string", "public")
                username = request.POST.get("username")
                password = request.POST.get("password")
                authentication_type = request.POST.get("authentication_type", "SHA")
                encryption_type = request.POST.get("encryption_type", "AES")
                encryption_key = request.POST.get("encryption_key")
                context_name = request.POST.get("context_name", "")
                oid = request.POST.get("oid", "1.3.6.1")
                
                try:
                    # Handle SNMP Version and append results
                    if snmp_version in ["1", "2c"]:
                        result = []
                        for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
                            SnmpEngine(),
                            CommunityData(read_community_string, mpModel=0 if snmp_version == "1" else 1),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False
                        ):
                            if errorIndication:
                                result.append(f"Error: {errorIndication}")
                                break
                            elif errorStatus:
                                result.append(f'Error: {errorStatus.prettyPrint()} at {errorIndex}')
                                break
                            else:
                                for varBind in varBinds:
                                    result.append(f"{varBind[0]} = {varBind[1]}")
                        results.append(f"<b>SNMP Walk Result:</b><pre>{' '.join(result)}</pre>")

                    elif snmp_version == "3":
                        auth_protocol = usmNoAuthProtocol
                        priv_protocol = usmNoPrivProtocol
                        if authentication_type == "MD5":
                            auth_protocol = usmHMACMD5AuthProtocol
                        elif authentication_type == "SHA":
                            auth_protocol = usmHMACSHAAuthProtocol
                        if encryption_type == "AES":
                            priv_protocol = usmAesCfb128Protocol
                        elif encryption_type == "DES":
                            priv_protocol = usmDESPrivProtocol

                        result = []
                        for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
                            SnmpEngine(),
                            UsmUserData(username, password, encryption_key, authProtocol=auth_protocol, privProtocol=priv_protocol),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ContextData(context_name),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False
                        ):
                            if errorIndication:
                                result.append(f"Error: {errorIndication}")
                                break
                            elif errorStatus:
                                result.append(f'Error: {errorStatus.prettyPrint()} at {errorIndex}')
                                break
                            else:
                                for varBind in varBinds:
                                    result.append(f"{varBind[0]} = {varBind[1]}")
                        results.append(f"<b>SNMP Walk Result:</b><pre>{' '.join(result)}</pre>")

                    else:
                        results.append(f"<b>Unsupported SNMP version:</b> {snmp_version}<br>")

                except Exception as e:
                    logging.error(f"An error occurred while performing SNMP walk: {str(e)}")
                    results.append(f"<b>Error:</b> {str(e)}<br>")
            results = [result.replace('\n', '<br>') for result in results]
            return render(request, "ping.html", {"results": results})

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.error(f"Network operation failed: {error_message}")
            return render(
                request, "ping.html", {"error_message": error_message}
            )
    else:
        return render(request, "ping.html")
