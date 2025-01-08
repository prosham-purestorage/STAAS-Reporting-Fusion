# This file is part of STAAS-Reporting-Fusion.
#
# STAAS-Reporting-Fusion is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# STAAS-Reporting-Fusion is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with STAAS-Reporting-Fusion. If not, see <http://www.gnu.org/licenses/>.

import staascommon
import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

from staas-common import check_admin_level, initialize_client

debug=4

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
    # See if there are any of the tags we are adding already on the volume        
    #response = client.get_volumes_tags(context_names=fleet_member, resource_names=volume_list, namespaces=namespace)
    # Check the response
    #if response.status_code != 200:
        # The tag check didn't work
    #    print(f"Failed to retrieve tags from {fleet_member},{volume_list}. Status code: {response.status_code}, Error: {response.errors}")
    #    return
    #else:
        # Remove the existing chargeback tag
        # response = client.delete_volumes_tags(context_names=fleet_member, resource_names=volume_list, namespaces=namespace, keys=key)
        # Check the response
        #if response.status_code == 202:
        #    if debug >=4:
        #        print(f"Tags removed successfully to volume {fleet_member},{volume_list},{tags}.")
        #else:
        #    print(f"Couldn't remove tags from volume {fleet_member},{volume_list},{tags}.")

    # Add the chargeback tag
    response = client.put_volumes_tags_batch(context_names=fleet_member, resource_names=volume_list, tag=tags)
    # Check the response
    if response.status_code == 200:
        if debug >=4:
            print(f"Tags added successfully to volume {fleet_member},{volume_list},{tags}.")
    else:
        print(f"Failed to add tags to {fleet_member},{volume_list},{tags}. Status code: {response.status_code}, Error: {response.errors}")
    

# Go through all volumes on this host and create an array of tags with volume names according to the tagging plan
def process_volumes(fleet_member):
    tag_set={}
    response = client.get_volumes(context_names=fleet_member.member.name)
    if response.status_code == 200:
        if debug >=2:
            print(f"finding volumes for array {fleet_member.member.name}")
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
            if fleet_member.member.name not in tag_set[tag_value]:
                tag_set[tag_value][fleet_member.member.name]=[]
            tag_set[tag_value][fleet_member.member.name].append(volume.name)
        
        if debug >= 3:
            print(f"Tagging array {fleet_member.member.name} volume {volume.name}, in namespace {NAMESPACE} with tag {TAG_KEY}: {tag_value}")

    # Tag the volumes by tag value
    for tag_value,bucket in tag_set.items():
        for bucket_name, volume_names in bucket.items():
            if debug >= 2:
                print(f"tag_volume({fleet_member.member.name}, {volume_names}, {tag_value}")                           
        tag_volume(fleet_member.member.name, volume_names, tag_value)                           

def list_fleets():
    # Retrieve the list of fleets, then find all of the FlashArrays and volumes associated with the fleet
    response = client.get_fleets_members()
    if response.status_code == 200:
        fleets_members=response.items
    else:
        print(f"Failed to retrieve fleets/members. Status code: {response.status_code}, Error: {response.errors}")
    return(fleets_members)

    
# Function to check admin level
def check_admin_level(desired_role):
    try:
        response = client.get_admins()
        if response.status_code == 200:
            admins = response.items
            for admin in admins:
                if admin.name == USER_NAME:
                    if debug >= 1:
                        print(f'User {USER_NAME} has admin level: {admin.role}')
                    if admin.role == desired_role:
                        return True
                    else:
        elif response.status_code == 400:
            print(f'Failed to get admins: {response.errors}')
            return False
    except PureError as e:
        print(f'Error checking admin level: {e}')

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
    # Read the Excel file
    spreadsheet = pd.ExcelFile('STAAS_Tagging.xlsx')
    # Extract global variables from the Fleet sheet
    fleet_df = spreadsheet.parse('Fleet')

    global_variables = fleet_df.iloc[0].to_dict()

    # Assign global variables
    USER_NAME = os.getenv('PURE_USER_NAME')
    API_TOKEN = os.getenv('PURE_API_TOKEN')
    print(f"USER_NAME: {USER_NAME}")
    print(f"API_TOKEN: {API_TOKEN}")
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')

    # Create a tagging plan from the Tagging_map sheet
    tags_df = spreadsheet.parse('Tagging_map')
    # Construct the dictionary of tagging rules
    for index, row in tags_df.iterrows():
        tag_by = row['Tag_By']
        container_name = row['Container_Name']
        tag_value = str(row['Tag_Value'])
        if tag_by not in TAGGING_RULES:
            TAGGING_RULES[tag_by] = {}
        TAGGING_RULES[tag_by][container_name] = tag_value

    try:
        # Initialize the client
        client = Client(FUSION_SERVER,username=USER_NAME, api_token=API_TOKEN)
    except PureError as e:
        print(f"Error initializing client: {e}")
    # Check to see minimum version of 2.38 & array admin privileges for this user
    if not check_admin_level("array_admin"):
        exit(1)
    if not check_api_version(2.38):
        exit(2)
    if not TAGGING_RULES or not TAGGING_RULES.get("default"):
        print(f"No tagging rules found")
        exit(3)

    # Get the arrays for reporting contexts for the nominated fleet
    for member in list_fleets():
        process_volumes(member)