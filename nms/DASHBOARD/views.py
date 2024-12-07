from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
import subprocess
import platform
import logging
import socket
from prettytable import PrettyTable

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

from django.contrib import messages

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")  # Replace 'login' with the name of your login URL


@login_required
def ping_operation(request):
    if request.method == "POST":
        get_ip_address = request.POST.get("ip_address")
        enable_ping = request.POST.get("enable_ping")
        verbose_ping = request.POST.get("verbose_ping")
        traceroute = request.POST.get("traceroute")
        dns_lookup = request.POST.get("dns_lookup")
        verbos_dns_lookup = request.POST.get("verbos_dns_lookup")
        snmp_walk = request.POST.get("snmp_walk")
        simple_snmp_walk = request.POST.get("simple_snmp_walk")
        # Get all DNS names as a list
        dns_names = list(DNS.objects.values_list("dns_name", flat=True))

        # Validate that the IP address or hostname does not have invalid spaces
        if " " in get_ip_address:
            messages.error(request, "Valid IP Address or Hostname is required.")
            return render(
                request,
                "ping.html",
                {"error_message": "IP address or hostname cannot contain spaces."},
            )

        # Validate the IP address format (IPv4)
        try:
            # If it's an IP address, validate it
            socket.inet_aton(get_ip_address)  # This raises socket.error if the IP is invalid
            ip_address = get_ip_address  # Use directly if valid IP
        except socket.error:
            try:
                # Resolve the hostname to an IP
                ip_address = socket.gethostbyname(get_ip_address)
            except socket.gaierror:
                logger.error(f"Failed to resolve hostname: {get_ip_address}")
                messages.error(request, "Valid IP Address or Hostname is required.")
                return render(
                    request,
                    "ping.html",
                    {"error_message": "Invalid IP address or hostname provided."},
                )

        print("Resolved IP Address:", ip_address)

        # Detect the operating system
        os_name = platform.system()
        results = []

        try:
            # Create a PrettyTable for formatting output
            table = PrettyTable()
            table.field_names = ["Operation", "Result"]

            # Perform Enable Ping
            if enable_ping:
                if os_name == "Windows":
                    command = ["ping", "-n", "1", ip_address]
                else:
                    command = ["ping", "-c", "1", ip_address]

                logger.info(f"Pinging {ip_address} with basic ping.")
                response = subprocess.run(command, capture_output=True, text=True)
                ping_result = (
                    "Device is alive"
                    if response.returncode == 0
                    else "Device is unreachable"
                )
                table.add_row(["Enable Ping", ping_result])

            # Perform Verbose Ping
            if verbose_ping:
                if os_name == "Windows":
                    command = ["ping", "-n", "4", ip_address]
                else:
                    command = ["ping", "-c", "4", ip_address]

                logger.info(f"Pinging {ip_address} with verbose ping.")
                response = subprocess.run(command, capture_output=True, text=True)
                verbose_result = (
                    response.stdout
                    if response.returncode == 0
                    else "Verbose Ping failed."
                )
                table.add_row(["Verbose Ping Result", verbose_result])

            # Perform Traceroute
            if traceroute:
                if os_name == "Windows":
                    command = ["tracert", ip_address]
                else:
                    command = ["traceroute", "-I", ip_address]

                logger.info(f"Running traceroute for {ip_address}.")
                response = subprocess.run(command, capture_output=True, text=True)
                traceroute_result = (
                    response.stdout
                    if response.returncode == 0
                    else "Traceroute failed."
                )
                table.add_row(["Traceroute Result", traceroute_result])

            # Perform DNS Lookup
            if dns_lookup:
                try:
                    # Determine the command based on OS
                    command = ["nslookup", ip_address]

                    # Execute the DNS query
                    response = subprocess.run(command, capture_output=True, text=True)

                    if response.returncode == 0:
                        # Extract the resolved IP from the output
                        dns_result = response.stdout.replace(
                            "Authoritative answers can be found from:", ""
                        )
                        logger.info("DNS query executed successfully.")

                        # Check if any resolved IP matches DNS records
                        if any(dns_ip in dns_result for dns_ip in dns_names):
                            table.add_row(["DNS Lookup Result", dns_result])
                        else:
                            table.add_row(
                                [
                                    "DNS Lookup Result",
                                    "Resolved IP does not match DNS records.",
                                ]
                            )
                    else:
                        table.add_row(["DNS Lookup Result", "DNS query failed."])
                except Exception as e:
                    table.add_row(["Unexpected Error", f"{str(e)}"])
            # perform verbos dns
            if verbos_dns_lookup:
                try:
                    command = ["dig", ip_address]

                    # Execute the DNS query
                    response = subprocess.run(command, capture_output=True, text=True)

                    if response.returncode == 0:
                        # Extract the resolved IP from the output
                        dns_result = response.stdout
                        logger.info("Verbose DNS query executed successfully.")

                        # Check if any resolved IP matches DNS records
                        if any(dns_ip in dns_result for dns_ip in dns_names):
                            table.add_row(["Verbose DNS Lookup Result", dns_result])
                        else:
                            table.add_row(
                                [
                                    "Verbose DNS Lookup Result",
                                    "Resolved IP does not match Verbose DNS records.",
                                ]
                            )
                    else:
                        table.add_row(
                            ["Verbose DNS Lookup Result", "DNS query failed."]
                        )
                except Exception as e:
                    table.add_row(["Unexpected Error", f"{str(e)}"])
            # Perform SNMP Walk
            if snmp_walk:
                snmp_port = 161  # default port for SNMP
                snmp_version = request.POST.get("snmp_version")
                read_community_string = request.POST.get(
                    "read_community_string", "public"
                )
                username = request.POST.get("username")
                password = request.POST.get("password")
                authentication_type = request.POST.get("authentication_type", "SHA")
                encryption_type = request.POST.get("encryption_type", "AES")
                encryption_key = request.POST.get("encryption_key")
                oid = request.POST.get("oid")

                try:
                    # Initialize result list
                    snmp_result = []

                    # SNMP Version 2c
                    if snmp_version == "1":
                        for (
                            errorIndication,
                            errorStatus,
                            errorIndex,
                            varBinds,
                        ) in nextCmd(
                            SnmpEngine(),
                            CommunityData(
                                "public",
                                mpModel=0 if snmp_version == "1" else 1,
                            ),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False,
                        ):
                            if errorIndication:
                                snmp_result.append(f"Error: {errorIndication}")
                                break
                            elif errorStatus:
                                snmp_result.append(
                                    f"Error: {errorStatus.prettyPrint()} at {errorIndex}"
                                )
                                break
                            else:
                                for varBind in varBinds:
                                    snmp_result.append(f"{varBind[0]} = {varBind[1]}")

                    # SNMP Version 3
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

                        for (
                            errorIndication,
                            errorStatus,
                            errorIndex,
                            varBinds,
                        ) in nextCmd(
                            SnmpEngine(),
                            UsmUserData(
                                username,
                                password,
                                encryption_key,
                                authProtocol=auth_protocol,
                                privProtocol=priv_protocol,
                            ),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False,
                        ):
                            if errorIndication:
                                snmp_result.append(f"Error: {errorIndication}")
                                break
                            elif errorStatus:
                                snmp_result.append(
                                    f"Error: {errorStatus.prettyPrint()} at {errorIndex}"
                                )
                                break
                            else:
                                for varBind in varBinds:
                                    snmp_result.append(f"{varBind[0]} = {varBind[1]}")

                    # Unsupported SNMP Version
                    else:
                        snmp_result.append(f"Unsupported SNMP version: {snmp_version}")

                    # Check if the response contains valid results
                    if snmp_result and not any(
                        "Error" in result for result in snmp_result
                    ):
                        # Redirect to snmp_results.html with results
                        table.add_row(["SNMP Walk Result", "\n".join(snmp_result)])
                    else:
                        # Append the error message to the table
                        table.add_row(["SNMP Walk Result", "\n".join(snmp_result)])

                except Exception as e:
                    logger.error(
                        f"An error occurred while performing SNMP walk: {str(e)}"
                    )
                    table.add_row(["SNMP Walk Result", f"Error: {str(e)}"])
            
            if simple_snmp_walk:
                snmp_port = 161  # default port for SNMP
                snmp_version = request.POST.get("snmp_version")
                read_community_string = request.POST.get(
                    "read_community_string", "public"
                )
                username = request.POST.get("username")
                password = request.POST.get("password")
                authentication_type = request.POST.get("authentication_type", "SHA")
                encryption_type = request.POST.get("encryption_type", "AES")
                encryption_key = request.POST.get("encryption_key")
                oid = request.POST.get("oid")

                try:
                    # Initialize result list
                    snmp_result = []

                    # SNMP Version 2c
                    if snmp_version == "1":
                        for (
                            errorIndication,
                            errorStatus,
                            errorIndex,
                            varBinds,
                        ) in nextCmd(
                            SnmpEngine(),
                            CommunityData(
                                "public",
                                mpModel=0 if snmp_version == "1" else 1,
                            ),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid)),
                            lexicographicMode=False,
                        ):
                            if errorIndication:
                                snmp_result.append(f"Error: {errorIndication}")
                                break
                            elif errorStatus:
                                snmp_result.append(
                                    f"Error: {errorStatus.prettyPrint()} at {errorIndex}"
                                )
                                break
                            else:
                                for varBind in varBinds:
                                    snmp_result.append(f"{varBind[0]} = {varBind[1]}")

                    # Check if the response contains valid results
                    if snmp_result and not any(
                        "Error" in result for result in snmp_result
                    ):
                        # Redirect to snmp_results.html with results
                        table.add_row(["SNMP Walk Result", "\n".join(snmp_result)])
                    else:
                        # Append the error message to the table
                        table.add_row(["SNMP Walk Result", "\n".join(snmp_result)])

                except Exception as e:
                    logger.error(
                        f"An error occurred while performing SNMP walk: {str(e)}"
                    )
                    table.add_row(["SNMP Walk Result", f"Error: {str(e)}"])

            # If no valid SNMP response, render ping.html
            return render(request, "ping.html", {"table": table})

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.error(f"Network operation failed: {error_message}")
            return render(request, "ping.html", {"error_message": error_message})
    else:
        return render(request, "ping.html")


def snmp_results(request):
    return render(request, "snmp_results.html")
