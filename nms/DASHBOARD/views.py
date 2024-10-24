# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
import subprocess
import platform
import logging
import socket
import struct

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
        ip_range_start = request.POST.get("ip_range_start")
        ip_range_end = request.POST.get("ip_range_end")
        enable_ping = request.POST.get("enable_ping")
        verbose_ping = request.POST.get("verbose_ping")
        traceroute = request.POST.get("traceroute")
        dns_lookup = request.POST.get("dns_lookup")
        snmp_walk = request.POST.get("snmp_walk")

        # Validate IP range input
        if not ip_range_start or not ip_range_end:
            return render(request, "ping.html", {"error_message": "Please provide a valid IP range."})

        try:
            # Convert IPs to integer for easier iteration
            start_ip = struct.unpack("!I", socket.inet_aton(ip_range_start))[0]
            end_ip = struct.unpack("!I", socket.inet_aton(ip_range_end))[0]

            if start_ip > end_ip:
                return render(request, "ping.html", {"error_message": "Start IP should be less than or equal to End IP."})

            # Limit the number of IPs to scan
            max_devices = 100
            device_count = min(max_devices, end_ip - start_ip + 1)

            os_name = platform.system()
            results = {}

            # Get SNMP parameters from POST
            snmp_port = request.POST.get("snmp_port")
            snmp_version = request.POST.get("snmp_version")
            read_community_string = request.POST.get("read_community_string")
            username = request.POST.get("username")
            password = request.POST.get("password")
            authentication_type = request.POST.get("authentication_type")
            encryption_type = request.POST.get("encryption_type")
            encryption_key = request.POST.get("encryption_key")
            context_name = request.POST.get("context_name")
            oid = request.POST.get("oid")

            # Iterate through the IP range
            for ip_int in range(start_ip, start_ip + device_count):
                ip_address = socket.inet_ntoa(struct.pack("!I", ip_int))
                ip_results = []

                try:
                    # Perform Enable Ping
                    if enable_ping:
                        ping_command = ["ping", "-c", "1" if os_name != "Windows" else "-n", "1", ip_address]
                        logger.info(f"Pinging {ip_address} with basic ping.")
                        ping_response = subprocess.run(ping_command, capture_output=True, text=True)

                        if ping_response.returncode == 0:
                            ip_results.append("Enable Ping: Device is alive")
                        else:
                            ip_results.append("Enable Ping: Device is unreachable")

                    # Perform Verbose Ping
                    if verbose_ping:
                        verbose_command = ["ping", "-c", "4" if os_name != "Windows" else "-n", "4", ip_address]
                        logger.info(f"Pinging {ip_address} with verbose ping.")
                        verbose_response = subprocess.run(verbose_command, capture_output=True, text=True)
                        ip_results.append(f"Verbose Ping Result:\n{verbose_response.stdout}")

                    # Perform Traceroute
                    if traceroute:
                        traceroute_command = ["traceroute" if os_name != "Windows" else "tracert", ip_address]
                        logger.info(f"Running traceroute to {ip_address}.")
                        traceroute_response = subprocess.run(traceroute_command, capture_output=True, text=True)
                        ip_results.append(f"Traceroute Result:\n{traceroute_response.stdout}")

                    # Perform DNS Lookup
                    if dns_lookup:
                        try:
                            hostname = socket.gethostbyaddr(ip_address)[0]
                            ip_results.append(f"DNS Lookup: {hostname}")
                        except socket.herror:
                            ip_results.append("DNS Lookup: Hostname not found")

                    # Perform SNMP Walk
                    if snmp_walk:
                        result = []
                        if snmp_version in ["1", "2c"]:
                            # SNMP v1 or v2c
                            for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
                                SnmpEngine(),
                                CommunityData(read_community_string, mpModel=0 if snmp_version == "1" else 1),
                                UdpTransportTarget((ip_address, int(snmp_port))),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid)),
                                lexicographicMode=False,
                            ):
                                if errorIndication:
                                    result.append(f"Error: {errorIndication}")
                                    break
                                elif errorStatus:
                                    result.append(
                                        f'Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}'
                                    )
                                    break
                                else:
                                    for varBind in varBinds:
                                        result.append(f"{varBind[0]} = {varBind[1]}")

                        elif snmp_version == "3":
                            # SNMP v3 with optional authentication and encryption
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

                            for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
                                SnmpEngine(),
                                UsmUserData(
                                    username,
                                    password,
                                    encryption_key,
                                    authProtocol=auth_protocol,
                                    privProtocol=priv_protocol,
                                ),
                                UdpTransportTarget((ip_address, int(snmp_port))),
                                ContextData(context_name),
                                ObjectType(ObjectIdentity(oid)),
                                lexicographicMode=False,
                            ):
                                if errorIndication:
                                    result.append(f"Error: {errorIndication}")
                                    break
                                elif errorStatus:
                                    result.append(
                                        f'Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or "?"}'
                                    )
                                    break
                                else:
                                    for varBind in varBinds:
                                        result.append(f"{varBind[0]} = {varBind[1]}")

                        ip_results.append("SNMP Walk Result:\n" + "\n".join(result))

                    # Collect results for this IP
                    results[ip_address] = "\n".join(ip_results)

                except Exception as ip_exception:
                    logger.error(f"Error with {ip_address}: {str(ip_exception)}")
                    results[ip_address] = f"An error occurred: {str(ip_exception)}"

            return render(request, "ping.html", {"results": results})

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.error(f"Network operation error: {str(e)}")
            return render(request, "ping.html", {"error_message": error_message})

    return render(request, "ping.html")