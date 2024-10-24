# dashboard/views.py

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
import subprocess
import platform
import logging
from netmiko import ConnectHandler
import ipaddress  # Importing the ipaddress module

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


def perform_ping(ip_address, count=1):
    os_name = platform.system()
    command = ["ping", "-n", str(count), ip_address] if os_name == "Windows" else ["ping", "-c", str(count), ip_address]
    response = subprocess.run(command, capture_output=True, text=True)
    return response

def perform_traceroute(ip_address):
    os_name = platform.system()
    command = ["tracert", ip_address] if os_name == "Windows" else ["traceroute", ip_address]
    response = subprocess.run(command, capture_output=True, text=True)
    return response

def perform_dns_lookup(ip_address):
    os_name = platform.system()
    command = ["nslookup", ip_address] if os_name == "Windows" else ["dig", ip_address]
    response = subprocess.run(command, capture_output=True, text=True)
    return response

def perform_snmp_walk(ip_address, snmp_port, snmp_version, read_community_string, oid, **kwargs):
    result = []
    if snmp_version in ["1", "2c"]:
        for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
            SnmpEngine(),
            CommunityData(read_community_string, mpModel=0 if snmp_version == "1" else 1),
            UdpTransportTarget((ip_address, snmp_port)),
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
        auth_protocol = usmNoAuthProtocol
        priv_protocol = usmNoPrivProtocol

        if kwargs.get("authentication_type") == "MD5":
            auth_protocol = usmHMACMD5AuthProtocol
        elif kwargs.get("authentication_type") == "SHA":
            auth_protocol = usmHMACSHAAuthProtocol

        if kwargs.get("encryption_type") == "AES":
            priv_protocol = usmAesCfb128Protocol
        elif kwargs.get("encryption_type") == "DES":
            priv_protocol = usmDESPrivProtocol

        for errorIndication, errorStatus, errorIndex, varBinds in nextCmd(
            SnmpEngine(),
            UsmUserData(
                kwargs.get("username"),
                kwargs.get("password"),
                kwargs.get("encryption_key"),
                authProtocol=auth_protocol,
                privProtocol=priv_protocol,
            ),
            UdpTransportTarget((ip_address, snmp_port)),
            ContextData(kwargs.get("context_name")),
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

    return result

def run_netmiko_command(ip_address, username, password, command):
    device = {
        'device_type': 'cisco_ios',  # Change this based on your device
        'host': ip_address,
        'username': username,
        'password': password,
    }
    
    try:
        connection = ConnectHandler(**device)
        output = connection.send_command(command)
        connection.disconnect()
        return output
    except Exception as e:
        return f"Error: {str(e)}"

def generate_ip_range(start_ip, end_ip):
    try:
        # Convert start and end IPs to IPv4Address objects
        start = ipaddress.IPv4Address(start_ip)
        end = ipaddress.IPv4Address(end_ip)

        # Generate all IPs in the range, including the end IP, by converting integer back to IP
        ip_range = [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]

        return ip_range
    except ValueError as e:
        logger.error(f"Invalid IP range: {e}")
        return []

    
@login_required
def ping_operation(request):
    if request.method == "POST":
        start_ip = request.POST.get("start_ip")
        end_ip = request.POST.get("end_ip")
        enable_ping = request.POST.get("enable_ping")
        verbose_ping = request.POST.get("verbose_ping")
        traceroute = request.POST.get("traceroute")
        dns_lookup = request.POST.get("dns_lookup")
        snmp_walk = request.POST.get("snmp_walk")
        ssh_username = request.POST.get("ssh_username")
        ssh_password = request.POST.get("ssh_password")
        command = request.POST.get("command")

        if not start_ip or not end_ip:
            return render(request, "ping.html", {"error_message": "Please provide both start and end IP addresses."})

        try:
            # Generate the IP range including the end IP
            ip_range = generate_ip_range(start_ip, end_ip)
            if not ip_range:
                return render(request, "ping.html", {"error_message": "Invalid IP range."})
            
            results = ""

            for ip in ip_range:
                # Perform Enable Ping
                if enable_ping:
                    response = perform_ping(ip, count=1)
                    results += f"Enable Ping {ip}: Device is alive\n" if response.returncode == 0 else f"Enable Ping {ip}: Device is unreachable\n"

                # Perform Verbose Ping
                if verbose_ping:
                    response = perform_ping(ip, count=4)
                    results += f"Verbose Ping Result {ip}:\n{response.stdout}\n" if response.returncode == 0 else f"Verbose Ping {ip} failed.\n"

                # Perform Traceroute
                if traceroute:
                    response = perform_traceroute(ip)
                    results += f"Traceroute Result {ip}:\n{response.stdout}\n" if response.returncode == 0 else f"Traceroute {ip} failed.\n"

                # Perform DNS Lookup
                if dns_lookup:
                    response = perform_dns_lookup(ip)
                    results += f"DNS Lookup Result {ip}:\n{response.stdout}\n" if response.returncode == 0 else f"DNS Lookup {ip} failed.\n"

                # Perform SNMP Walk
                if snmp_walk:
                    snmp_port = int(request.POST.get("snmp_port"))
                    snmp_version = request.POST.get("snmp_version")
                    read_community_string = request.POST.get("read_community_string")
                    oid = request.POST.get("oid")
                    result = perform_snmp_walk(
                        ip,
                        snmp_port,
                        snmp_version,
                        read_community_string,
                        oid,
                        username=request.POST.get("username"),
                        password=request.POST.get("password"),
                        authentication_type=request.POST.get("authentication_type"),
                        encryption_type=request.POST.get("encryption_type"),
                        encryption_key=request.POST.get("encryption_key"),
                        context_name=request.POST.get("context_name"),
                    )
                    results += f"\nSNMP Walk Result {ip}:\n" + "\n".join(result) + "\n"

                # Perform SSH Command using Netmiko
                if command:
                    ssh_output = run_netmiko_command(ip, ssh_username, ssh_password, command)
                    results += f"SSH Command Result {ip}:\n{ssh_output}\n"

            return render(request, "ping.html", {"results": results})

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            logger.error(f"Network operation error: {str(e)}")
            return render(request, "ping.html", {"error_message": error_message})
    return render(request, "ping.html")