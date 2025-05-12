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
import asyncio
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

# Separate function for validating IP addresses
def validate_ip_addresses(get_ip_address_all, request):
    ip_addresses = []
    for item in get_ip_address_all:
        try:
            # Validate if it's an IPv4 address
            socket.inet_aton(item)
            ip_addresses.append(item)
        except socket.error:
            try:
                # Attempt to resolve hostname to IP
                resolved_ip = socket.gethostbyname(item)
                ip_addresses.append(resolved_ip)
            except socket.gaierror:
                logger.error(f"Failed to resolve hostname: {item}")
                messages.warning(request, f"Could not resolve: {item}")
                continue  # Skip invalid hostname, but don't fail all
    return list(set(ip_addresses))  # Deduplicate

# Separate function for Enable Ping operation
async def enable_ping_operation(ip_addresses, os_name, table):
    async def ping_device(ip_address):
        command = ["ping", "-n", "1", ip_address] if os_name == "Windows" else ["ping", "-c", "1", ip_address]
        logger.info(f"Pinging {ip_address} with basic ping.")
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode == 0:
                return ip_address, "Device is alive"
            else:
                return ip_address, "Device is unreachable"
        except Exception as e:
            return ip_address, f"Error: {str(e)}"
    
    tasks = [ping_device(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    for ip_address, ping_result in results:
        table.add_row([f"Enable Ping Result for {ip_address}", ping_result])


async def verbose_ping_operation(ip_addresses, os_name, table):
    async def ping_device(ip_address):
        command = ["ping", "-n", "4", ip_address] if os_name == "Windows" else ["ping", "-c", "4", ip_address]
        logger.info(f"Pinging {ip_address} with verbose ping.")
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return ip_address, stdout.decode().strip()
            else:
                return ip_address, "Verbose Ping failed."
        except Exception as e:
            return ip_address, f"Error: {str(e)}"
    
    tasks = [ping_device(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    for ip_address, ping_result in results:
        table.add_row([f"Verbose Ping Result for {ip_address}", ping_result])

# Separate function for Traceroute operation
async def traceroute_operation(ip_addresses, os_name, table):
    async def run_traceroute(ip_address):
        command = ["tracert", ip_address] if os_name == "Windows" else ["traceroute", "-I", ip_address]
        logger.info(f"Running traceroute for {ip_address}.")
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return ip_address, stdout.decode().strip()
            else:
                return ip_address, "Traceroute failed."
        except Exception as e:
            return ip_address, f"Error: {str(e)}"
    
    tasks = [run_traceroute(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    for ip_address, traceroute_result in results:
        table.add_row([f"Traceroute Result for {ip_address}", traceroute_result])

# Separate function for DNS Lookup operation
async def dns_lookup_operation(ip_addresses, table):
    async def lookup_dns(ip_address):
        try:
            command_reverse = ["nslookup", ip_address]
            process = await asyncio.create_subprocess_exec(
                *command_reverse,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                reverse_dns_result = stdout.decode().replace("Authoritative answers can be found from:", "")
                logger.info(f"Reverse DNS query executed successfully for {ip_address}.")
                return ip_address, reverse_dns_result
            else:
                logger.warning(f"Reverse DNS query failed for {ip_address}.")
                return ip_address, "Reverse DNS query failed."
        except Exception as e:
            logger.error(f"Error during DNS lookup for {ip_address}: {str(e)}")
            return ip_address, f"Error: {str(e)}"
    
    tasks = [lookup_dns(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    for ip_address, dns_result in results:
        table.add_row([f"Reverse DNS Lookup Result for {ip_address}", dns_result])

# Separate function for Verbose DNS Lookup operation
async def verbose_dns_lookup_operation(ip_addresses, table):
    async def lookup_verbose_dns(ip_address):
        command_reverse_verbose = [
            "dig",
            "-x",
            ip_address,
            "+noall",
            "+answer",
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *command_reverse_verbose,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                reverse_dns_result_verbose = stdout.decode().strip()
                logger.info(f"Verbose Reverse DNS query executed successfully for {ip_address}.")
                return ip_address, reverse_dns_result_verbose if reverse_dns_result_verbose else "No answer received."
            else:
                error_message = stderr.decode().strip() or "Verbose Reverse DNS query failed."
                logger.warning(f"Verbose Reverse DNS query failed for {ip_address}: {error_message}")
                return ip_address, error_message
        except Exception as e:
            error_message = f"Error: {str(e)}"
            logger.error(f"Error during verbose DNS lookup for {ip_address}: {error_message}")
            return ip_address, error_message
    
    tasks = [lookup_verbose_dns(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    for ip_address, dns_result in results:
        table.add_row([f"Verbose Reverse DNS Lookup Result for {ip_address}", dns_result])

# Separate function for Advanced SNMP Walk
async def advanced_snmp_walk(ip_addresses, snmp_version, community_strings, username, password, authentication_type, encryption_type, encryption_key, oid, snmp_port, table):
    async def snmp_walk(ip_address):
        snmp_result = []
        try:
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
            result_message = "\n".join(snmp_result) if snmp_result else "No SNMP data returned."
            return ip_address, result_message

        except Exception as e:
            logger.error(f"An error occurred while performing SNMP walk for {ip_address}: {str(e)}")
            return ip_address, f"Error: {str(e)}"

    tasks = [snmp_walk(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)

    # Add results to the table
    for ip_address, result_message in results:
        table.add_row([f"SNMP Walk Result for {ip_address}", result_message])
# Separate function for Simple SNMP Walk
async def simple_snmp_walk(ip_addresses, snmp_port, table):
    async def snmp_walk(ip_address, community_strings, hardcoded_oid, snmp_version):
        snmp_result = []
        try:
            if snmp_version == 'v2c':
                for community_string in community_strings:
                    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                        SnmpEngine(),
                        CommunityData(community_string, mpModel=1),
                        UdpTransportTarget((ip_address, int(snmp_port))),
                        ContextData(),
                        ObjectType(ObjectIdentity(hardcoded_oid).loadMibs('SNMPv2-MIB')),
                        lexicographicMode=False,
                    ):
                        if errorIndication:
                            logger.error(f'SNMPv2c Walk Error for {ip_address} with community "{community_string}": {str(errorIndication)}')
                            return f'Error: {str(errorIndication)}'
                        elif errorStatus:
                            logger.error(f'SNMPv2c Error at {errorIndex} for {ip_address} with community "{community_string}": {errorStatus.prettyPrint()}')
                            return f'Error: {errorStatus.prettyPrint()}'
                        else:
                            for varBind in varBinds:
                                snmp_result.append(f'{varBind[0].prettyPrint()} = {varBind[1]}')
            else:
                v3_user = 'myUser'
                v3_auth_password = 'myAuthPass'
                v3_priv_password = 'myPrivPass'
                for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                    SnmpEngine(),
                    UsmUserData(v3_user, authKey=v3_auth_password, privKey=v3_priv_password,
                    authProtocol=usmHMACSHAAuthProtocol, privProtocol=usmAesCfb128Protocol),
                    UdpTransportTarget((ip_address, int(snmp_port))),
                    ContextData(),
                    ObjectType(ObjectIdentity(hardcoded_oid).loadMibs('SNMPv2-MIB')),
                    lexicographicMode=False,
                ):
                    if errorIndication:
                        logger.error(f'SNMPv3 Walk Error for {ip_address}: {str(errorIndication)}')
                        return f'Error: {str(errorIndication)}'
                    elif errorStatus:
                        logger.error(f'SNMPv3 Error at {errorIndex} for {ip_address}: {errorStatus.prettyPrint()}')
                        return f'Error: {errorStatus.prettyPrint()}'
                    else:
                        for varBind in varBinds:
                            snmp_result.append(f'{varBind[0].prettyPrint()} = {varBind[1]}')
            return snmp_result
        except Exception as e:
            logger.error(f'An error occurred during SNMP walk for {ip_address}: {str(e)}')
            return f'Error: {str(e)}'

    community_strings = ['public', 'private']
    hardcoded_oid = '1.3.6.1.2.1.1'

    tasks = [snmp_walk(ip, community_strings, hardcoded_oid, 'v2c') for ip in ip_addresses]
    results = await asyncio.gather(*tasks)

    for ip_address, snmp_result in zip(ip_addresses, results):
        if isinstance(snmp_result, list) and snmp_result:
            table.add_row([f'Simple SNMP Walk Result for {ip_address}', '\n'.join(snmp_result)])
        else:
            table.add_row([f'Simple SNMP Walk Result for {ip_address}', snmp_result])

    # Process SNMPv3 if needed
    tasks_v3 = [snmp_walk(ip, community_strings, hardcoded_oid, 'v3') for ip in ip_addresses]
    results_v3 = await asyncio.gather(*tasks_v3)

    for ip_address, snmp_result_v3 in zip(ip_addresses, results_v3):
        if isinstance(snmp_result_v3, list) and snmp_result_v3:
            table.add_row([f'Simple SNMPv3 Walk Result for {ip_address}', '\n'.join(snmp_result_v3)])
        else:
            table.add_row([f'Simple SNMPv3 Walk Result for {ip_address}', snmp_result_v3])
@login_required
def ping_operation(request):
    if request.method == "POST":
        get_ip_address_start = request.POST.get("start_ip_address")
        get_ip_address_all = generate_ip_list(get_ip_address_start)

        enable_ping = request.POST.get("enable_ping")
        verbose_ping = request.POST.get("verbose_ping")
        traceroute = request.POST.get("traceroute")
        dns_lookup = request.POST.get("dns_lookup")
        verbos_dns_lookup = request.POST.get("verbos_dns_lookup")
        snmp_walk = request.POST.get("snmp_walk")
        is_simple_snmp_walk = request.POST.get("simple_snmp_walk")

        # Validate the IP addresses / hostnames
        ip_addresses = validate_ip_addresses(get_ip_address_all, request)
        if not ip_addresses:
            return render(request, "ping.html", {
                "error_message": "No valid IP address or hostname found."
            })

        os_name = platform.system()

        table = PrettyTable()
        table.field_names = ["Operation", "Result"]

        try:
            async def perform_operations():
                if enable_ping:
                    try:
                        await enable_ping_operation(ip_addresses, os_name, table)
                    except Exception as e:
                        table.add_row(["Enable Ping", f"Error: {str(e)}"] )

                if verbose_ping:
                    try:
                        await verbose_ping_operation(ip_addresses, os_name, table)
                    except Exception as e:
                        table.add_row(["Verbose Ping", f"Error: {str(e)}"])

                if traceroute:
                    try:
                        await traceroute_operation(ip_addresses, os_name, table)
                    except Exception as e:
                        table.add_row(["Traceroute", f"Error: {str(e)}"])

                if dns_lookup:
                    try:
                        await dns_lookup_operation(ip_addresses, table)
                    except Exception as e:
                        table.add_row(["DNS Lookup", f"Error: {str(e)}"])

                if verbos_dns_lookup:
                    try:
                        await verbose_dns_lookup_operation(ip_addresses, table)
                    except Exception as e:
                        table.add_row(["Verbose DNS Lookup", f"Error: {str(e)}"])

                if snmp_walk:
                    try:
                        await advanced_snmp_walk(
                            ip_addresses,
                            snmp_version=request.POST.get("snmp_version"),
                            community_strings=request.POST.getlist("community_strings", ["public", "private"]),
                            username=request.POST.get("username"),
                            password=request.POST.get("password"),
                            authentication_type=request.POST.get("authentication_type", "SHA"),
                            encryption_type=request.POST.get("encryption_type", "AES"),
                            encryption_key=request.POST.get("encryption_key"),
                            oid=request.POST.get("oid"),
                            snmp_port=161,
                            table=table
                        )
                    except Exception as e:
                        table.add_row(["Advanced SNMP Walk", f"Error: {str(e)}"])

                if is_simple_snmp_walk:
                    try:
                        await simple_snmp_walk(ip_addresses, '161', table)
                    except Exception as e:
                        table.add_row(["Simple SNMP Walk", f"Error: {str(e)}"])

            asyncio.run(perform_operations())

            return render(request, "ping.html", {"table": table})

        except Exception as e:
            logger.exception("Unexpected error in network operations")
            return render(request, "ping.html", {"error_message": f"An unexpected error occurred: {str(e)}"})

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

