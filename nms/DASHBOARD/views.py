from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
import subprocess
import platform
import logging
import socket
from prettytable import PrettyTable

from django.core.mail import send_mail
from django.http import JsonResponse
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# Set up logging
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
from ipaddress import ip_address



def generate_ip_list(ip_input):
    """Parses input of multiple IPs or IP ranges and returns a list of IPs."""
    ip_list = []
    
    # Split by comma to handle multiple IPs
    parts = ip_input.split(',')
    
    for part in parts:
        part = part.strip()
        
        # Check if it's a range (denoted by '-')
        if '-' in part:
            try:
                start_ip, end_ip = part.split('-')
                start_ip = ip_address(start_ip.strip())
                end_ip = ip_address(end_ip.strip())

                if start_ip > end_ip:
                    raise ValueError(f"Invalid range: {start_ip} - {end_ip}")

                # Generate and add the range of IPs
                ip_list.extend([str(ip_address(ip)) for ip in range(int(start_ip), int(end_ip) + 1)])

            except ValueError as e:
                print(f"Error: {e}")
        
        else:
            # Single IP case
            try:
                ip = ip_address(part)
                ip_list.append(str(ip))
            except ValueError:
                print(f"Invalid IP address: {part}")

    return ip_list


@login_required
def ping_operation(request):
    if request.method == "POST":
        get_ip_address_start = request.POST.get("start_ip_address")
        get_ip_address_all = generate_ip_list(get_ip_address_start)

        print("line 62", get_ip_address_all)

        enable_ping = request.POST.get("enable_ping")
        verbose_ping = request.POST.get("verbose_ping")
        traceroute = request.POST.get("traceroute")
        dns_lookup = request.POST.get("dns_lookup")
        verbos_dns_lookup = request.POST.get("verbos_dns_lookup")
        snmp_walk = request.POST.get("snmp_walk")
        simple_snmp_walk = request.POST.get("simple_snmp_walk")
        # Get all DNS names as a list

        # Validate that the IP address or hostname does not have invalid spaces
        if any(" " in ip for ip in get_ip_address_all):
            messages.error(request, "Valid IP Address or Hostname is required.")
            logger.error("Valid IP Address or Hostname is required.")
            return render(
                request,
                "ping.html",
                {"error_message": "IP address or hostname cannot contain spaces."},
            )

        # Validate the IP address format (IPv4)
        ip_addresses = []

        for item in get_ip_address_all:
            try:
                # If it's an IP address, validate it
                socket.inet_aton(item)  # This raises socket.error if the IP is invalid
                ip_addresses.append(item)  # Use directly if valid IP
            except socket.error:
                try:
                    # Resolve the hostname to an IP
                    resolved_ip = socket.gethostbyname(item)
                    ip_addresses.append(resolved_ip)
                except socket.gaierror:
                    logger.error(f"Failed to resolve hostname: {item}")
                    messages.error(request, "Valid IP Address or Hostname is required.")
                    logger.error("Invalid IP address or hostname provided.")
                    return render(
                        request,
                        "ping.html",
                        {"error_message": "Invalid IP address or hostname provided."},
                    )

        print("Resolved IP Addresses:", ip_addresses)


        # Detect the operating system
        os_name = platform.system()
        results = []

        try:
            # Create a PrettyTable for formatting output
            table = PrettyTable()
            table.field_names = ["Operation", "Result"]

            try:
                # Perform Enable Ping
                if enable_ping:
                    for ip_address in ip_addresses:
                        command = ["ping", "-n", "1", ip_address] if os_name == "Windows" else ["ping", "-c", "1", ip_address]
                        logger.info(f"Pinging {ip_address} with basic ping.")
                        try:
                            response = subprocess.run(command, capture_output=True, text=True, check=True)
                            ping_result = "Device is alive"
                        except subprocess.CalledProcessError:
                            ping_result = "Device is unreachable"
                        except Exception as e:
                            ping_result = f"Error: {str(e)}"
                        table.add_row([f"Enable Ping Result for {ip_address}", ping_result])
            except Exception as e:
                table.add_row(["General Error", f"An error occurred: {str(e)}"])


            try:
                # Perform Verbose Ping
                if verbose_ping:
                    for ip_address in ip_addresses:
                        if os_name == "Windows":
                            command = ["ping", "-n", "4", ip_address]
                        else:
                            command = ["ping", "-c", "4", ip_address]

                        logger.info(f"Pinging {ip_address} with verbose ping.")
                        try:
                            response = subprocess.run(command, capture_output=True, text=True, check=True)
                            verbose_result = response.stdout
                        except subprocess.CalledProcessError:
                            verbose_result = "Verbose Ping failed."
                        except Exception as e:
                            verbose_result = f"Error: {str(e)}"
                        table.add_row([f"Verbose Ping Result for {ip_address}", verbose_result])
            except Exception as e:
                table.add_row(["General Error", f"An error occurred: {str(e)}"])

           
            try:
                # Perform Traceroute
                if traceroute:
                    for ip_address in ip_addresses:
                        if os_name == "Windows":
                            command = ["tracert", ip_address]
                        else:
                            command = ["traceroute", "-I", ip_address]

                        logger.info(f"Running traceroute for {ip_address}.")
                        try:
                            response = subprocess.run(command, capture_output=True, text=True, check=True)
                            traceroute_result = response.stdout
                        except subprocess.CalledProcessError:
                            traceroute_result = "Traceroute failed."
                        except Exception as e:
                            traceroute_result = f"Error: {str(e)}"
                        table.add_row([f"Traceroute Result for {ip_address}", traceroute_result])
            except Exception as e:
                table.add_row(["General Error", f"An error occurred: {str(e)}"])

                
            try:
                # Perform DNS Lookup
                if dns_lookup:
                    for ip_address in ip_addresses:
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
                            response_reverse = subprocess.run(command_reverse, capture_output=True, text=True)

                            if response_reverse.returncode == 0:
                                reverse_dns_result = response_reverse.stdout.replace(
                                    "Authoritative answers can be found from:", ""
                                )
                                logger.info(f"Reverse DNS query executed successfully for {ip_address}.")
                                table.add_row([f"Reverse DNS Lookup Result for {ip_address}", reverse_dns_result])
                            else:
                                logger.warning(f"Reverse DNS query failed for {ip_address}.")
                                table.add_row([f"Reverse DNS Lookup Result for {ip_address}", "Reverse DNS query failed."])

                        except subprocess.CalledProcessError as e:
                            logger.error(f"Subprocess Error during DNS lookup for {ip_address}: {str(e)}")
                            table.add_row([f"Reverse DNS Lookup Result for {ip_address}", f"Subprocess Error: {str(e)}"])

                        except Exception as e:
                            logger.error(f"Unexpected Error during DNS lookup for {ip_address}: {str(e)}")
                            table.add_row([f"Reverse DNS Lookup Result for {ip_address}", f"Unexpected Error: {str(e)}"])

            except Exception as e:
                logger.error(f"General Error during DNS lookup process: {str(e)}")
                table.add_row(["General Error", f"An error occurred during the DNS lookup process: {str(e)}"])

            

            try:
                # Perform Verbose DNS Lookup
                if verbos_dns_lookup:
                    for ip_address in ip_addresses:
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
                                logger.info(f"Verbose Reverse DNS query executed successfully for {ip_address}.")
                                table.add_row(
                                    [
                                        f"Verbose Reverse DNS Lookup Result for {ip_address}",
                                        reverse_dns_result_verbose,
                                    ]
                                )
                            else:
                                logger.warning(f"Verbose Reverse DNS query failed for {ip_address}.")
                                table.add_row(
                                    [
                                        f"Verbose Reverse DNS Lookup Result for {ip_address}",
                                        "Verbose Reverse DNS query failed.",
                                    ]
                                )

                        except subprocess.CalledProcessError as e:
                            logger.error(f"Subprocess Error during verbose DNS lookup for {ip_address}: {str(e)}")
                            table.add_row(
                                [
                                    f"Verbose Reverse DNS Lookup Result for {ip_address}",
                                    f"Subprocess Error: {str(e)}",
                                ]
                            )

                        except Exception as e:
                            logger.error(f"Unexpected Error during verbose DNS lookup for {ip_address}: {str(e)}")
                            table.add_row(
                                [
                                    f"Verbose Reverse DNS Lookup Result for {ip_address}",
                                    f"Unexpected Error: {str(e)}",
                                ]
                            )

            except Exception as e:
                logger.error(f"General Error during verbose DNS lookup process: {str(e)}")
                table.add_row(["General Error", f"An error occurred during the verbose DNS lookup process: {str(e)}"])

            

            try:
                # Advance SNMP Walk
                if snmp_walk:
                    for ip_address in ip_addresses:
                        snmp_port = 161  # Default port for SNMP
                        snmp_version = request.POST.get("snmp_version")
                        community_strings = request.POST.getlist("community_strings", ["public", "private"])  # add more if needed
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
                                    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
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
                                            snmp_result.append(f"SNMP Error: {errorIndication}")
                                            logger.error(f"SNMP Error: {errorIndication}")
                                            break
                                        elif errorStatus:
                                            snmp_result.append(f"SNMP Error at {errorIndex}: {errorStatus.prettyPrint()}")
                                            logger.error(f"SNMP Error at {errorIndex}: {errorStatus.prettyPrint()}")
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

                                    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                                        SnmpEngine(),
                                        UsmUserData(
                                            username,
                                            password,
                                            encryption_key,
                                            authProtocol=auth_protocol,
                                            privProtocol=priv_protocol,
                                        ),
                                        UdpTransportTarget((ip_address, int(snmp_port))),
                                        ContextData(),
                                        ObjectType(ObjectIdentity(oid)),
                                        lexicographicMode=False,
                                    ):
                                        if errorIndication:
                                            snmp_result.append(f"SNMP Error: {errorIndication}")
                                            logger.error(f"SNMP Error: {errorIndication}")
                                            break
                                        elif errorStatus:
                                            snmp_result.append(f"SNMP Error at {errorIndex}: {errorStatus.prettyPrint()}")
                                            logger.error(f"SNMP Error at {errorIndex}: {errorStatus.prettyPrint()}")
                                            break
                                        else:
                                            for varBind in varBinds:
                                                snmp_result.append(f"{varBind[0]} = {varBind[1]}")

                                # Unsupported SNMP Version
                                else:
                                    snmp_result.append(f"Unsupported SNMP version: {snmp_version}")
                                    logger.error(f"Unsupported SNMP version: {snmp_version}")

                            # Check if results contain errors
                            if snmp_result:
                                result_message = "\n".join(snmp_result)
                            else:
                                result_message = "No SNMP data returned."

                            table.add_row([f"SNMP Walk Result for {ip_address}", result_message])

                        except Exception as e:
                            logger.error(f"An error occurred while performing SNMP walk for {ip_address}: {str(e)}")
                            table.add_row([f"SNMP Walk Result for {ip_address}", f"Error: {str(e)}"])

            except Exception as e:
                logger.error(f"General error during SNMP walk process: {str(e)}")
                table.add_row(["General Error", f"An error occurred during the SNMP walk process: {str(e)}"])

            

            try:
                # Simple SNMP
                if simple_snmp_walk:
                    for ip_address in ip_addresses:
                        snmp_port = 161  # Default port for SNMP
                        community_strings = ["public", "private"]  # Predefined community strings
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
                                    ObjectType(ObjectIdentity(hardcoded_oid).loadMibs("SNMPv2-MIB")),
                                    lexicographicMode=False,
                                ):
                                    if errorIndication:
                                        logger.error(f"SNMPv2c Walk Error for {ip_address} with community '{community_string}': {str(errorIndication)}")
                                        table.add_row([f"SNMP Walk Result for {ip_address}", f"Error: {str(errorIndication)}"])
                                        snmp_walk_successful = False
                                        break
                                    elif errorStatus:
                                        logger.error(f"SNMPv2c Error at {errorIndex} for {ip_address} with community '{community_string}': {errorStatus.prettyPrint()}")
                                        table.add_row([f"SNMP Walk Result for {ip_address}", f"Error: {errorStatus.prettyPrint()}"])
                                        snmp_walk_successful = False
                                        break
                                    else:
                                        for varBind in varBinds:
                                            # Use the resolved name instead of raw OID
                                            snmp_result.append(f"{varBind[0].prettyPrint()} = {varBind[1]}")

                                if snmp_result:
                                    snmp_walk_successful = True
                                    break

                            # If SNMPv2c was successful, process the result
                            if snmp_walk_successful:
                                table.add_row([f"Simple SNMP Walk Result for {ip_address}", "\n".join(snmp_result)])
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
                                    ObjectType(ObjectIdentity(hardcoded_oid).loadMibs("SNMPv2-MIB")),
                                    lexicographicMode=False,
                                ):
                                    if errorIndication:
                                        logger.error(f"SNMPv3 Walk Error for {ip_address}: {str(errorIndication)}")
                                        table.add_row([f"SNMPv3 Walk Result for {ip_address}", f"Error: {str(errorIndication)}"])
                                        break
                                    elif errorStatus:
                                        logger.error(f"SNMPv3 Error at {errorIndex} for {ip_address}: {errorStatus.prettyPrint()}")
                                        table.add_row([f"SNMPv3 Walk Result for {ip_address}", f"Error: {errorStatus.prettyPrint()}"])
                                        break
                                    else:
                                        for varBind in varBinds:
                                            # Use the resolved name instead of raw OID
                                            snmp_result_v3.append(f"{varBind[0].prettyPrint()} = {varBind[1]}")

                                # Process SNMPv3 result
                                if snmp_result_v3:
                                    table.add_row([f"Simple SNMPv3 Walk Result for {ip_address}", "\n".join(snmp_result_v3)])
                                else:
                                    table.add_row([f"Simple SNMPv3 Walk Result for {ip_address}", "No valid response."])

                        except Exception as e:
                            logger.error(f"An error occurred during Simple SNMP Walk for {ip_address}: {str(e)}")
                            table.add_row([f"Simple SNMP Walk Result for {ip_address}", f"Error: {str(e)}"])
            except Exception as e:
                logger.error(f"General error during SNMP walk process: {str(e)}")
                table.add_row(["General Error", f"An error occurred during the SNMP walk process: {str(e)}"])



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



@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        try:
            # Parse the JSON request body
            data = json.loads(request.body)
            email_list = data.get('email_list', [])
            email_body = data.get('email_body', '')

            if not email_list or not email_body:
                return JsonResponse({'success': False, 'message': 'Invalid input'}, status=400)

            # Send email to all email addresses in the list
            print("line 535, ", email_list)
            print("line 536", email_body)
            send_mail(
                subject="Results from Web Page",
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,  # Use the same email as in settings
                recipient_list=email_list,
            )

            return JsonResponse({'success': True, 'message': 'Email sent successfully!'})
        
        except Exception as e:
            # Log the error for debugging
            print(f"Error sending email: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

