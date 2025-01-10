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
# POSSIBILITY OF SUCH DAMAGE.

import os
import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

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

debug=2

# If the volume is in a realm or pod, grab those names
def match_volume_name(volume_name):
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
    if tag_by in TAGGING_RULES and container_name in TAGGING_RULES[tag_by]:
        return TAGGING_RULES[tag_by][container_name]
    return None

def tag_volume(fleet_member,volume_list,value):
    tags = [
        {"namespace": NAMESPACE, "key": TAG_KEY, "value": value}
    ]
    # Add the chargeback tag
    response = client.put_volumes_tags_batch(context_names=[fleet_member], resource_names=volume_list, tag=tags)
    # Check the response
    if response.status_code == 200:
        if debug >=4:
            print(f"Tags added successfully to volume {fleet_member},{volume_list},{tags}.")
    else:
        print(f"Failed to add tags to {fleet_member},{volume_list},{tags}. Status code: {response.status_code}, Error: {response.errors}")
    

# Go through all volumes on this host and create an array of tags with volume names according to the tagging plan
def process_volumes(fleet_member):
    tag_set={}
    response = client.get_volumes(context_names=fleet_member)
    if response.status_code == 200:
        if debug >=2:
            print(f"finding volumes for array {fleet_member}")
        volumes = response.items
    else:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")
        return
    
    for volume in volumes:
        if volume.subtype != 'regular':
            if debug >= 4:
                print(f'Non-regular volume {volume.name} found - not tagging it.')
            continue;
        result = match_volume_name(volume.name)
        volume_group = volume.volume_group
        
        realm = result.get("realm")
        pod = result.get("pod")
        if realm:
            tag_value = get_tag_value("realm", realm)
            if tag_value:
                if debug >= 5:
                    print(f'Tag value for realm {realm}: {tag_value}')
            else:
                if debug >= 5:
                    print(f'No tagging rule found for realm {realm}')
                tag_value = get_tag_value("default", "default")

            if tag_value not in tag_set:
                tag_set[tag_value]={}
            if realm not in tag_set[tag_value]:
                tag_set[tag_value][realm]=[]
            tag_set[tag_value][realm].append(volume.name)

        elif pod:
            tag_value = get_tag_value("pod", pod)
            if tag_value: 
                if debug >= 5:
                    print(f'Tag value for pod {pod}: {tag_value}')
            else:
                if debug >= 5:
                    print(f'No tagging rule found for pod {pod}')                
                tag_value = get_tag_value("default", "default")

            if tag_value not in tag_set:
                tag_set[tag_value]={}
            if pod not in tag_set[tag_value]:
                tag_set[tag_value][pod]=[]
            tag_set[tag_value][pod].append(volume.name)
        else:
            if debug >= 5:
                print(f'Plain volume name: {volume.name}')
            tag_value = get_tag_value("default", "default")
            if tag_value not in tag_set:
                tag_set[tag_value]={}
            if fleet_member not in tag_set[tag_value]:
                tag_set[tag_value][fleet_member]=[]
            tag_set[tag_value][fleet_member].append(volume.name)
        
        if debug >= 3:
            print(f"Tagging array {fleet_member} volume {volume.name}, in namespace {NAMESPACE} with tag {TAG_KEY}: {tag_value}")

    # Tag the volumes by tag value
    for tag_value,bucket in tag_set.items():
        for bucket_name, volume_names in bucket.items():
            if debug >= 2:
                print(f"tag_volume({fleet_member}, {volume_names}, {tag_value}")                           
        tag_volume(fleet_member, volume_names, tag_value)                           

USER_NAME=""
TAG_API_TOKEN=""
FUSION_SERVER=""
NAMESPACE=""
TAG_KEY = "chargeback"
TAGGING_RULES = {}

# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Main script
if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments("config")

    # Read the configuration file
    config_path = os.path.join(args.config)
    # Read the Excel file
    config_spreadsheet = pd.ExcelFile(config_path)
    # Extract global variables from the Fleet sheet
    fleet_df = config_spreadsheet.parse('Fleet')

    global_variables = fleet_df.iloc[0].to_dict()

    # Assign global variables
    USER_NAME = os.getenv('PURE_USER_NAME')
    API_TOKEN = os.getenv('PURE_API_TOKEN')
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')

    # Create a tagging plan from the Tagging_map sheet
    tags_df = config_spreadsheet.parse('Tagging_map')
    # Construct the dictionary of tagging rules
    for index, row in tags_df.iterrows():
        tag_by = row['Tag_By']
        container_name = row['Container_Name']
        tag_value = str(row['Tag_Value'])
        if tag_by not in TAGGING_RULES:
            TAGGING_RULES[tag_by] = {}
        TAGGING_RULES[tag_by][container_name] = tag_value

    # Check to see that we can open a connection, with array admin privileges for this user & minimum FA API version of 2.38 
    client = initialise_client(FUSION_SERVER,USER_NAME, API_TOKEN)
    if not client:
        exit(1)
    role = check_purity_role(client, USER_NAME)
    if not role == "array_admin":
        exit(2)
    if not check_api_version(client, 2.39):
        exit(3)
    if not TAGGING_RULES or not TAGGING_RULES.get("default"):
        print(f"No tagging rules found")
        exit(4)

    # Get the arrays for reporting contexts for the nominated fleet
    fleets = list_fleets(client)
    fleet_members = list_members(client,fleets)
    
    for fleet_member in fleet_members:
        process_volumes(fleet_member)