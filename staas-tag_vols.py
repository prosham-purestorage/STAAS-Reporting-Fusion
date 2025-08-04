# This file is part of STAAS-Reporting-Fusion.
#
# STAAS-Reporting-Fusion is licensed under the BSD 2-Clause License.
# You may obtain a copy of the License at
#
#     https://opensource.org/licenses/BSD-2-Clause
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE

import os
import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

"""
staas-tag_vols.py
-----------------
Tags block volumes in a Pure Storage Fusion fleet for chargeback, based on rules in a spreadsheet.
Tagging is prioritized by realm, pod, workload, host group, host, and default.

Usage:
    python staas-tag_vols.py --config config/STAAS_Config.xlsx

See README.md for more details.
"""

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError
from staas_common import (
    parse_arguments,
    check_purity_role,
    check_api_version,
    initialise_client,
    list_fleets,
    list_members
)

USER_NAME=""
API_TOKEN=""
FUSION_SERVER=""
NAMESPACE=""
TAG_KEY = "chargeback"
TAGGING_RULES = {}
host_group_volumes_by_volume = {}
host_volumes_by_volume = {}
debug=7

# If the volume is in a realm or pod, grab those names
def match_volume_name(volume_name):
    """
    Parse a volume name to extract realm, pod, and volume components.
    Args:
        volume_name: The name of the volume
    Returns:
        dict with keys 'realm', 'pod', 'volume'
    """
    realmpattern = r'^([\w.-]+)::([\w.-]+)::([\w.-]+)$'
    podpattern = r'^([\w.-]+)::([\w.-]+)$'
    volpattern = r'^[\w-]+(?:/[\w-]+)*$'
    
    match = re.match(realmpattern, volume_name)
    if match:
        groups = match.groups()
        return {
            'realm': groups[0],
            'pod': groups[1],
            'volume': groups[2]
        }

    match = re.match(podpattern, volume_name)
    if match:
        groups = match.groups()
        return {
            'realm': None,
            'pod': groups[0],
            'volume': groups[1]
        }

    match = re.match(volpattern, volume_name)
    if match:
        return {
            'realm': None,
            'pod': None,
            'volume': volume_name
        }
    
# get the tag value for any tagging_rule
def get_tag_value(tag_by, container_name):
    """
    Get the tag value for a given tag type and container name from TAGGING_RULES.
    """
    if tag_by in TAGGING_RULES and container_name in TAGGING_RULES[tag_by]:
        return TAGGING_RULES[tag_by][container_name]
    return None

def tag_volume(client,fleet_member, volume_list, value):
    """
    Apply a chargeback tag to a list of volumes on a fleet member.
    """
    tags = [
        {"namespace": NAMESPACE, "key": TAG_KEY, "value": value}
    ]
    chunk_size = 100  # Adjust the chunk size as needed

    for i in range(0, len(volume_list), chunk_size):
        volume_chunk = volume_list[i:i + chunk_size]
        # Add the chargeback tag
        response = client.put_volumes_tags_batch(context_names=[fleet_member], resource_names=volume_chunk, tag=tags)
        # Check the response
        if response.status_code == 200:
            if debug >= 4:
                print(f"Tags added successfully to volume {fleet_member},{volume_chunk},{tags}.")
        else:
            print(f"Failed to add tags to {fleet_member},{volume_chunk},{tags}. Status code: {response.status_code}, Error: {response.errors}")
            break

def get_host_group_volumes_by_volume(client, fleet_member):
    """
    Retrieve volumes for each host group in TAGGING_RULES and index them by volume name.
    Args:
        client: Fusion API client
        fleet_member: Name of the array
    Returns:
        dict mapping volume name to host group name
    """
    """
    Retrieve volumes for each host group in TAGGING_RULES and index them by volume name.

    Args:
        client (Client): The Pure Storage FlashArray client.
        fleet_member (str): The name of the fleet member.

    Returns:
        dict: A dictionary where the keys are volume names and the values are host group names.
    """
    host_group_volumes_by_volume = {}
    host_groups_for_tagging = TAGGING_RULES.get("host_group", {})

    response_host_groups = client.get_host_groups(context_names=[fleet_member])
    if response_host_groups.status_code == 200:
        host_groups = response_host_groups.items
        host_group_names = [host_group.name for host_group in host_groups]  # Extract the names
        if debug >= 3:
            print(f"Host group names: {host_group_names}")
    else:
        print(f"Failed to retrieve host groups. Status code: {response_host_groups.status_code}, Error: {response_host_groups.errors}")
        return
    
    # Retrieve volumes for each host group
    for host_group_name in host_group_names:
        if host_group_name in host_groups_for_tagging.keys():
            response_connections = client.get_connections(context_names=[fleet_member], host_group_names=[host_group_name])
            if response_connections.status_code == 200:
                volumes = response_connections.items
                for volume in volumes:
                    host_group_volumes_by_volume[volume.volume.name] = host_group_name
            else:
                print(f"Failed to retrieve connections. Status code: {response_connections.status_code}, Error: {response_connections.errors}")
                return
    return host_group_volumes_by_volume

def match_host_group(volume_name):
    """
    Return the host group name for a given volume, if present.
    """
    if volume_name in host_group_volumes_by_volume:
        return host_group_volumes_by_volume[volume_name]
    return None

def get_host_volumes_by_volume(client, fleet_member):
    """
    Retrieve volumes for each host in TAGGING_RULES and index them by volume name.
    Args:
        client: Fusion API client
        fleet_member: Name of the array
    Returns:
        dict mapping volume name to host name
    """
    """
    Retrieve volumes for each host in TAGGING_RULES and index them by volume name.

    Args:
        client (Client): The Pure Storage FlashArray client.
        fleet_member (str): The name of the fleet member.

    Returns:
        dict: A dictionary where the keys are volume names and the values are host names.
    """
    host_volumes_by_volume = {}
    hosts_for_tagging = TAGGING_RULES.get("host", {})

    response_hosts = client.get_hosts(context_names=[fleet_member])
    if response_hosts.status_code == 200:
        hosts = response_hosts.items
        host_names = [host.name for host in hosts]  # Extract the names
        if debug >= 3:
            print(f"Host names: {host_names}")
    else:
        print(f"Failed to retrieve hosts. Status code: {response_hosts.status_code}, Error: {response_hosts.errors}")
        return
    
    # Retrieve volumes for each host
    for host_name in host_names:
        if host_name in hosts_for_tagging.keys():
            response_connections = client.get_connections(context_names=[fleet_member], host_names=[host_name])
            if response_connections.status_code == 200:
                connections = response_connections.items
                for connection in connections:
                    host_volumes_by_volume[connection.volume.name] = host_name
            else:
                print(f"Failed to retrieve connections. Status code: {response_connections.status_code}, Error: {response_connections.errors}")
                return
    return host_volumes_by_volume

def match_host(volume_name):
    """
    Return the host name for a given volume, if present.
    """
    if volume_name in host_volumes_by_volume:
        return host_volumes_by_volume[volume_name]
    return None

# Go through all volumes on this host and create an array of tags with volume names according to the tagging plan
def process_volumes(client, fleet_member):
    """
    For all regular volumes on a fleet member, determine the correct chargeback tag
    based on the tagging rules and apply the tag using the Fusion API.
    """
    tag_set = {}
    continuation_token = None  # Initialize the continuation token

    # Retrieve host group volumes indexed by volume name
    host_group_volumes_by_volume = get_host_group_volumes_by_volume(client, fleet_member)
    host_volumes_by_volume = get_host_volumes_by_volume(client, fleet_member)

    while True:
        # Retrieve volumes with pagination
        response = client.get_volumes(context_names=[fleet_member], continuation_token=continuation_token)
        if response.status_code == 200:
            if debug >= 2:
                print(f"Finding volumes for array {fleet_member} (Batch with continuation token: {continuation_token})")
            volumes = response.items
        else:
            print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")
            return

        for volume in volumes:
            if volume.subtype != 'regular':
                if debug >= 4:
                    print(f"Non-regular volume {volume.name} found - not tagging it.")
                continue

            # Match volume name to realm, pod, or other keys in TAGGING_RULES
            result = match_volume_name(volume.name)
            realm = result.get("realm")
            pod = result.get("pod")
            host_group_name = match_host_group(volume.name)
            host_name = match_host(volume.name)

            # Define the order of keys to check
            tagging_order = ["realm", "pod", "workload", "host_group", "host", "default"]

            # Loop through the keys in the defined order
            for key in tagging_order:
                if key == "realm" and realm in TAGGING_RULES["realm"]:
                    tag_value = get_tag_value("realm", realm)
                elif key == "pod" and pod in TAGGING_RULES["pod"]:
                    tag_value = get_tag_value("pod", pod)
                elif key == "workload":
                    # Add workload-specific logic here if needed
                    tag_value = None
                elif key == "host_group" and host_group_name:
                    # Add host_group-specific logic here if needed
                    tag_value = get_tag_value("host_group", host_group_name)
                elif key == "host":
                    # Add host-specific logic here if needed
                    tag_value = get_tag_value("host", host_name)
                elif key == "default":
                    tag_value = get_tag_value("default", "default")
                else:
                    continue

                if tag_value:
                    if debug >= 5:
                        print(f"Tag value for {key}: {tag_value}")
                    if tag_value not in tag_set:
                        tag_set[tag_value] = {}
                    if key not in tag_set[tag_value]:
                        tag_set[tag_value][key] = []
                    tag_set[tag_value][key].append(volume.name)
                    break  # Exit the loop once a match is found

            if debug >= 3:
                print(f"Tagging volume {volume.name} on array {fleet_member}, in namespace {NAMESPACE} with tag {TAG_KEY}: {tag_value}")

        # Check if there are more volumes to process
        continuation_token = response.continuation_token
        if not continuation_token:
            break  # Exit the loop if there are no more volumes

    # Tag the volumes by tag value
    for tag_value, bucket in tag_set.items():
        for bucket_name, volume_names in bucket.items():
            if debug >= 2:
                print(f"tag_volume({fleet_member}, {volume_names}, {tag_value})")
            tag_volume(client, fleet_member, volume_names, tag_value)

# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    """
    Main entry point for the tagging script. Loads config, tagging rules, and applies tags to all fleet members.
    """
    global NAMESPACE, TAGGING_RULES
    # Parse command-line arguments
    args = parse_arguments("tag_vols")

    # Read the configuration file
    config_path = os.path.join(args.config)
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        exit(1)

    config_spreadsheet = pd.ExcelFile(config_path)

    # Read the Excel file
    fleet_df = config_spreadsheet.parse('Fleet')

    # Extract global variables from the Fleet sheet
    global_variables = fleet_df.iloc[0].to_dict()

    # Assign global variables
    USER_NAME = os.getenv('PURE_USER_NAME')
    API_TOKEN = os.getenv('PURE_API_TOKEN')
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')

    # Read the Tagging_map worksheet
    tagging_map_df = config_spreadsheet.parse('Tagging_map')

    # Populate TAGGING_RULES
    TAGGING_RULES = {"realm": {}, "pod": {}, "workload": {}, "host_group": {}, "host": {}, "default": {}}
    for _, row in tagging_map_df.iterrows():
        tag_by = row.get("Tag_By", "").lower()  # e.g., "realm", "pod","host_group","host" or "default"
        container_name = row.get("Container_Name", "").strip()  # e.g., "realm1", "pod1"
        tag_value = str(row.get("Tag_Value", "")).strip()  # e.g., "TagValue1"

        if tag_by in TAGGING_RULES:
            TAGGING_RULES[tag_by][container_name] = tag_value
        else:
            print(f"Unknown Tag_By value: {tag_by}. Skipping row.")

    print(f"Loaded tagging rules: {TAGGING_RULES}")

    print(f"Connecting to Fusion server: {FUSION_SERVER} with user: {USER_NAME}")

    client = initialise_client(FUSION_SERVER, USER_NAME, API_TOKEN)
    if not client:
        exit(1)

    # Get the arrays for tagging contexts for the nominated fleet
    fleets = list_fleets(client)
    for fleet in fleets:
        fleet_members = list_members(client, [fleet])

        for fleet_member in fleet_members:
            process_volumes(client, fleet_member)

if __name__ == "__main__":
    main()