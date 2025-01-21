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
    logger.error("log out failed")
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
            logger.error("Valid IP Address or Hostname is required.")
            return render(
                request,
                "ping.html",
                {"error_message": "IP address or hostname cannot contain spaces."},
            )

        # Validate the IP address format (IPv4)
        try:
            # If it's an IP address, validate it
            socket.inet_aton(
                get_ip_address
            )  # This raises socket.error if the IP is invalid
            ip_address = get_ip_address  # Use directly if valid IP
        except socket.error:
            try:
                # Resolve the hostname to an IP
                ip_address = socket.gethostbyname(get_ip_address)
            except socket.gaierror:
                logger.error(f"Failed to resolve hostname: {get_ip_address}")
                messages.error(request, "Valid IP Address or Hostname is required.")
                logger.error("Invalid IP address or hostname provided.")
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
                    """
                    # Forward DNS Lookup: Resolve domain name from IP
                    command_forward = ["nslookup", ip_address]

                    # Execute Forward DNS query
                    response_forward = subprocess.run(
                        command_forward, capture_output=True, text=True
                    )

                    if response_forward.returncode == 0:
                        forward_dns_result = response_forward.stdout.replace(
                            "Authoritative answers can be found from:", ""
                        )
                        logger.info("Forward DNS query executed successfully.")

                        # Check if resolved domains match the expected DNS records
                        if any(dns_ip in forward_dns_result for dns_ip in dns_names):
                            table.add_row(
                                ["Forward DNS Lookup Result", forward_dns_result]
                            )
                        else:
                            table.add_row(
                                [
                                    "Forward DNS Lookup Result",
                                    "Resolved domain does not match expected DNS records.",
                                ]
                            )
                    else:
                        table.add_row(
                            ["Forward DNS Lookup Result", "Forward DNS query failed."]
                        )
                    """
                    # Reverse DNS Lookup: Resolve IP from domain name
                    command_reverse = ["nslookup", ip_address]

                    # Execute Reverse DNS query
                    response_reverse = subprocess.run(
                        command_reverse, capture_output=True, text=True
                    )

                    if response_reverse.returncode == 0:
                        reverse_dns_result = response_reverse.stdout.replace(
                            "Authoritative answers can be found from:", ""
                        )
                        logger.info("Reverse DNS query executed successfully.")
                        table.add_row(["Reverse DNS Lookup Result", reverse_dns_result])
                    else:
                        table.add_row(
                            ["Reverse DNS Lookup Result", "Reverse DNS query failed."]
                        )

                except Exception as e:
                    logger.error(f"Unexpected Error: {str(e)}")
                    table.add_row(["Unexpected Error", f"{str(e)}"])

            # Perform Verbose DNS Lookup
            if verbos_dns_lookup:
                try:
                    """
                    # Forward DNS Lookup
                    command_forward_verbose = ["dig", "+noall", "+answer", ip_address]

                    # Execute Forward DNS query
                    response_forward_verbose = subprocess.run(
                        command_forward_verbose, capture_output=True, text=True
                    )

                    if response_forward_verbose.returncode == 0:
                        forward_dns_result_verbose = response_forward_verbose.stdout
                        logger.info("Verbose Forward DNS query executed successfully.")

                        # Check if resolved domains match the expected DNS records
                        if any(
                            dns_ip in forward_dns_result_verbose for dns_ip in dns_names
                        ):
                            table.add_row(
                                [
                                    "Verbose Forward DNS Lookup Result",
                                    forward_dns_result_verbose,
                                ]
                            )
                        else:
                            table.add_row(
                                [
                                    "Verbose Forward DNS Lookup Result",
                                    "Resolved domain does not match expected verbose DNS records.",
                                ]
                            )
                    else:
                        table.add_row(
                            [
                                "Verbose Forward DNS Lookup Result",
                                "Verbose DNS query failed.",
                            ]
                        )
                    """
                    # Reverse DNS Lookup
                    command_reverse_verbose = [
                        "dig",
                        "-x",
                        ip_address,
                        "+noall",
                        "+answer",
                    ]

                    # Execute Reverse DNS query
                    response_reverse_verbose = subprocess.run(
                        command_reverse_verbose, capture_output=True, text=True
                    )

                    if response_reverse_verbose.returncode == 0:
                        reverse_dns_result_verbose = response_reverse_verbose.stdout
                        logger.info("Verbose Reverse DNS query executed successfully.")
                        table.add_row(
                            [
                                "Verbose Reverse DNS Lookup Result",
                                reverse_dns_result_verbose,
                            ]
                        )
                    else:
                        table.add_row(
                            [
                                "Verbose Reverse DNS Lookup Result",
                                "Verbose Reverse DNS query failed.",
                            ]
                        )

                except Exception as e:
                    logger.error(f"Unexpected Error: {str(e)}")
                    table.add_row(["Unexpected Error", f"{str(e)}"])

            # Advance SNMP Walk
            if snmp_walk:
                snmp_port = 161  # Default port for SNMP
                snmp_version = request.POST.get("snmp_version")
                community_strings = request.POST.getlist(
                    "community_strings", ["public", "private"]
                )  # add more here
                username = request.POST.get("username")
                password = request.POST.get("password")
                authentication_type = request.POST.get("authentication_type", "SHA")
                encryption_type = request.POST.get("encryption_type", "AES")
                encryption_key = request.POST.get("encryption_key")
                oid = request.POST.get("oid")

                try:
                    # Initialize result list
                    snmp_result = []

                    for community_string in community_strings:
                        # SNMP Version 1 or 2c
                        if snmp_version in ["1", "2c"]:
                            for (
                                errorIndication,
                                errorStatus,
                                errorIndex,
                                varBinds,
                            ) in nextCmd(
                                SnmpEngine(),
                                CommunityData(
                                    community_string,
                                    mpModel=0 if snmp_version == "1" else 1,
                                ),
                                UdpTransportTarget((ip_address, int(snmp_port))),
                                ContextData(),
                                ObjectType(ObjectIdentity(oid)),
                                lexicographicMode=False,
                            ):
                                if errorIndication:
                                    break
                                elif errorStatus:
                                    break
                                else:
                                    for varBind in varBinds:
                                        snmp_result.append(
                                            f"{varBind[0]} = {varBind[1]}"
                                        )
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
                                    break
                                elif errorStatus:
                                    snmp_result.append()
                                    break
                                else:
                                    for varBind in varBinds:
                                        snmp_result.append(
                                            f"{varBind[0]} = {varBind[1]}"
                                        )

                        # Unsupported SNMP Version
                        else:
                            snmp_result.append(
                                f"Unsupported SNMP version: {snmp_version}"
                            )
                            logger.error(f"Unsupported SNMP version: {snmp_version}")

                    # Check if the response contains valid results
                    if snmp_result and not any(
                        "Error" in result for result in snmp_result
                    ):
                        table.add_row(["SNMP Walk Result", "\n".join(snmp_result)])
                    else:
                        table.add_row(["SNMP Walk Result", "\n".join(snmp_result)])

                except Exception as e:
                    logger.error(
                        f"An error occurred while performing SNMP walk: {str(e)}"
                    )
                    table.add_row(["SNMP Walk Result", f"Error: {str(e)}"])
            # simple snmp
            if simple_snmp_walk:
                snmp_port = 161  # Default port for SNMP
                community_strings = [
                    "public",
                    "private",
                ]  # Predefined community strings
                hardcoded_oid = "1.3.6.1.2.1.1"  # Example OID for system information

                try:
                    # Initialize result list
                    snmp_result = []

                    # Attempt SNMPv2c walk
                    snmp_walk_successful = False
                    for community_string in community_strings:
                        for (
                            errorIndication,
                            errorStatus,
                            errorIndex,
                            varBinds,
                        ) in nextCmd(
                            SnmpEngine(),
                            CommunityData(community_string, mpModel=1),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ContextData(),
                            ObjectType(
                                ObjectIdentity(hardcoded_oid).loadMibs("SNMPv2-MIB")
                            ),
                            lexicographicMode=False,
                        ):
                            if errorIndication:
                                break
                            elif errorStatus:
                                break
                            else:
                                for varBind in varBinds:
                                    # Use the resolved name instead of raw OID
                                    snmp_result.append(
                                        f"{varBind[0].prettyPrint()} = {varBind[1]}"
                                    )
                        if snmp_result:
                            snmp_walk_successful = True
                            break

                    # If SNMPv2c was successful, process the result
                    if snmp_walk_successful:
                        # Check if the response contains valid results
                        if snmp_result and not any(
                            "Error" in result for result in snmp_result
                        ):
                            table.add_row(
                                ["Simple SNMP Walk Result", "\n".join(snmp_result)]
                            )
                        else:
                            table.add_row(
                                ["Simple SNMP Walk Result", "No valid response."]
                            )
                    else:
                        # If SNMPv2c fails, attempt SNMPv3
                        snmp_result_v3 = []
                        v3_user = "myUser"  # change this
                        v3_auth_password = "myAuthPass"  # change this
                        v3_priv_password = "myPrivPass"  # change this

                        for (
                            errorIndication,
                            errorStatus,
                            errorIndex,
                            varBinds,
                        ) in nextCmd(
                            SnmpEngine(),
                            UsmUserData(
                                v3_user,
                                authKey=v3_auth_password,
                                privKey=v3_priv_password,
                                authProtocol=usmHMACSHAAuthProtocol,
                                privProtocol=usmAesCfb128Protocol,
                            ),
                            UdpTransportTarget((ip_address, int(snmp_port))),
                            ContextData(),
                            ObjectType(
                                ObjectIdentity(hardcoded_oid).loadMibs("SNMPv2-MIB")
                            ),
                            lexicographicMode=False,
                        ):
                            if errorIndication:
                                break
                            elif errorStatus:
                                break
                            else:
                                for varBind in varBinds:
                                    # Use the resolved name instead of raw OID
                                    snmp_result_v3.append(
                                        f"{varBind[0].prettyPrint()} = {varBind[1]}"
                                    )

                        # Process SNMPv3 result
                        if snmp_result_v3 and not any(
                            "Error" in result for result in snmp_result_v3
                        ):
                            table.add_row(
                                ["Simple SNMPv3 Walk Result", "\n".join(snmp_result_v3)]
                            )
                        else:
                            table.add_row(
                                ["Simple SNMPv3 Walk Result", "No valid response."]
                            )

                except Exception as e:
                    logger.error(f"An error occurred during Simple SNMP Walk: {str(e)}")
                    table.add_row(["Simple SNMP Walk Result", f"Error: {str(e)}"])

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
