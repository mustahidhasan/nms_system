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
import re


def generate_ip_list(ip_input):
    """Parse input of IPs, ranges, or hostnames and return a list of targets."""
    ip_list = []
    if not ip_input:
        return ip_list

    parts = re.split(r"[,\s]+", ip_input.strip())

    for part in parts:
        if not part:
            continue
        candidate = part.strip()

        if "-" in candidate:
            start_str, end_str = candidate.split("-", 1)
            try:
                start_ip = ip_address(start_str.strip())
                end_ip = ip_address(end_str.strip())

                if start_ip > end_ip:
                    raise ValueError(f"Invalid range: {start_ip} - {end_ip}")

                ip_list.extend([str(ip_address(ip)) for ip in range(int(start_ip), int(end_ip) + 1)])
                continue
            except ValueError:
                # Fall back to treating the entry as hostname (e.g., FQDN with hyphen)
                pass

        try:
            ip = ip_address(candidate)
            ip_list.append(str(ip))
        except ValueError:
            # Not an IP; try to resolve later during validation
            ip_list.append(candidate)

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

# New function to perform MTR
async def run_mtr_for_ip(ip, table):
    try:
        command = ['mtr', '-r', '-c', '10', ip]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await asyncio.to_thread(process.communicate)

        if stderr:
            table.add_row([f"MTR - {ip}", f"Error: {stderr.decode('utf-8')}"])
        else:
            table.add_row([f"MTR - {ip}", stdout.decode('utf-8')])
    except Exception as e:
        table.add_row([f"MTR - {ip}", f"Exception: {str(e)}"])

async def mtr_operation(ip_addresses, table):
    tasks = [asyncio.create_task(run_mtr_for_ip(ip, table)) for ip in ip_addresses]
    await asyncio.gather(*tasks)

from django.conf import settings
from django.http import JsonResponse


@login_required
def ping_operation(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=405)

    get_ip_address_start = request.POST.get("start_ip_address")
    get_ip_address_all = generate_ip_list(get_ip_address_start)

    enable_ping = request.POST.get("enable_ping")
    verbose_ping = request.POST.get("verbose_ping")
    traceroute = request.POST.get("traceroute")
    dns_lookup = request.POST.get("dns_lookup")
    verbos_dns_lookup = request.POST.get("verbos_dns_lookup")
    snmp_walk = request.POST.get("snmp_walk")
    is_simple_snmp_walk = request.POST.get("simple_snmp_walk")
    mtr = request.POST.get("mtr")

    ip_addresses = validate_ip_addresses(get_ip_address_all, request)
    print("line 435", ip_addresses)
    if not ip_addresses:
        return JsonResponse({"error": "No valid IP address or hostname found."}, status=400)

    os_name = platform.system()
    table = PrettyTable()
    table.field_names = ["Operation", "Result"]
    results = []

    try:
        async def perform_operations():
            if enable_ping:
                try:
                    await enable_ping_operation(ip_addresses, os_name, table)
                except Exception as e:
                    results.append({"operation": "Enable Ping", "result": f"Error: {str(e)}"})

            if verbose_ping:
                try:
                    await verbose_ping_operation(ip_addresses, os_name, table)
                except Exception as e:
                    results.append({"operation": "Verbose Ping", "result": f"Error: {str(e)}"})

            if traceroute:
                try:
                    await traceroute_operation(ip_addresses, os_name, table)
                except Exception as e:
                    results.append({"operation": "Traceroute", "result": f"Error: {str(e)}"})

            if dns_lookup:
                try:
                    await dns_lookup_operation(ip_addresses, table)
                except Exception as e:
                    results.append({"operation": "DNS Lookup", "result": f"Error: {str(e)}"})

            if verbos_dns_lookup:
                try:
                    await verbose_dns_lookup_operation(ip_addresses, table)
                except Exception as e:
                    results.append({"operation": "Verbose DNS Lookup", "result": f"Error: {str(e)}"})

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
                    results.append({"operation": "Advanced SNMP Walk", "result": f"Error: {str(e)}"})

            if is_simple_snmp_walk:
                try:
                    await simple_snmp_walk(ip_addresses, '161', table)
                except Exception as e:
                    results.append({"operation": "Simple SNMP Walk", "result": f"Error: {str(e)}"})

            if mtr:
                try:
                    await mtr_operation(ip_addresses, table)
                except Exception as e:
                    results.append({"operation": "MTR", "result": f"Error: {str(e)}"})

        asyncio.run(perform_operations())

        # Convert PrettyTable to list of rows
        for row in table._rows:
            results.append({
                "operation": row[0],
                "result": row[1],
            })
        print("line 513", results)
        return JsonResponse({"success": True, "results": results})

    except Exception as e:
        logger.exception("Unexpected error in network operations")
        return JsonResponse({
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }, status=500)


def snmp_results(request):
    return JsonResponse({"message": "This would return SNMP results if implemented"})


@csrf_exempt
def send_email(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        email_list = data.get('email_list', [])
        email_body = data.get('email_body', '')

        if not email_list or not email_body:
            return JsonResponse({'success': False, 'message': 'Invalid input'}, status=400)

        send_mail(
            subject="Results from Web Page",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_list,
        )

        return JsonResponse({'success': True, 'message': 'Email sent successfully!'})

    except Exception as e:
        logger.exception("Error sending email")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)
