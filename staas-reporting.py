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

import staas-common

from datetime import datetime
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
    
def read_volume_tags(fleet_member_name, volumes):
    tags={}
    # Get any tags in the correct namespace for this array, and create a map of (array,volumes) to tags
    response = client.get_volumes_tags(context_names=fleet_member_name, resource_names=volumes, namespaces=NAMESPACE)
    # Check the response
    if response.status_code == 200:
        if debug >= 4:
            print(f"Tags from {fleet_member_name} in namespace {NAMESPACE}:")
            pp.pprint(response.items)
        # Process each tag, which has a context, key, value, namespace, and resource (of a volume)
        for tag in response.items:
            if tag.namespace == NAMESPACE and tag.key == TAG_KEY:
                volume=tag.resource.name
                tags[volume] = tag.value
    else:
        print(f"Failed to get tags from {fleet_member_name}. Status code: {response.status_code}, Error: {response.errors}")
    return tags

def get_volume_space(fleet_member_name, volumes):
    space_values={}
    response = client.get_volumes_space(context_names=fleet_member_name, names=volumes)
    if response.status_code == 200:
        if debug >= 2:
            print(f"Space values for volumes in array {fleet_member_name}")
        for volume in response.items:
            space_values[volume.name]=volume.space
    else:
        print(f"Failed to retrieve volume space. Status code: {response.status_code}, Error: {response.errors}")
    return space_values

def report_array(fleet_member_name):
    # Go through all volumes on this host and create an array of tags with volume names according to the tagging plan
    response = client.get_volumes(context_names=fleet_member_name)
    if response.status_code == 200:
        if debug >= 2:
            print(f"Finding volumes for array {fleet_member_name}")
        volumes = [volume.name for volume in response.items]
        tags = read_volume_tags(fleet_member_name, volumes)
        volumes = get_volume_space(fleet_member_name, volumes)

        for volume in volumes:
            SEEN_TAGS[fleet_member_name,volume] = {
                'tag',tags[volume],
                'space', {}
            }
            print(f"Volume: {volume}, Space: {space_value}, Chargeback Tag: {chargeback_tag}")
    else:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")

def report_volumes(fleet_member_name):
    # Go through all volumes on this host and create an array of tags with volume names according to the tagging plan
    response = client.get_volumes(context_names=fleet_member_name)
    if response.status_code == 200:
        if debug >= 2:
            print(f"Finding volumes for array {fleet_member_name}")

#        volumes = [volume.name for volume in response.items]
        for volume in response.items
            if volume.subtype != 'regular':
                if debug >= 4:
                    print(f'Non-regular volume {volume.name} found - not tagging it.')
                continue;    

        tags = read_volume_tags(fleet_member_name, volumes)
        volumes = get_volume_space(fleet_member_name, volumes)

        for volume in volumes:
            SEEN_TAGS[fleet_member_name,volume] = {
                'tag',tags[volume],
                'space', {}
            }
            print(f"Volume: {volume}, Space: {space_value}, Chargeback Tag: {chargeback_tag}")
    else:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")

def list_fleets():
    # Retrieve the list of fleets, then find all of the FlashArrays and volumes associated with the fleet
    response = client.get_fleets_members()
    if response.status_code == 200:
        fleets_members=response.items
    else:
        print(f"Failed to retrieve fleets/members. Status code: {response.status_code}, Error: {response.errors}")
    return(fleets_members)

# Check API version
def check_api_version(level):
    version = client.get_rest_version()
    
    if float(version) >= level:
        return True
    else:
        if debug >= 1:
            print(f'API Version: {version}')
            print(f"API version needs to support Fusion v2 at a minimum.")
        return False
    
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
SEEN_TAGS = {}
NOW=""

# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Main script
if __name__ == "__main__":
    # Read the Excel file
    tagging_spreadsheet = pd.ExcelFile('STAAS_Tagging.xlsx')
    reporting_spreadsheet = pd.ExcelFile('STAAS_Reporting.xlsx')
    # Extract global variables from the Fleet sheet
    fleet_df = tagging_spreadsheet.parse('Fleet')

    global_variables = fleet_df.iloc[0].to_dict()

    # Assign global variables
    USER_NAME = os.getenv('PURE_USER_NAME')
    API_TOKEN = os.getenv('PURE_API_TOKEN')
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')
    TAG_KEY = "chargeback"

    NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

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
        
    # Get the arrays for reporting contexts for the nominated fleet
    for fleet_member in list_fleets():
        report_volumes(fleet_member.member.name)