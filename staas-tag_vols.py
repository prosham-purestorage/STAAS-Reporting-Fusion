import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError


debug=2

# If the volume is in a realm or pod, grab those names
def match_volume_name(volume_name):
    pattern = r'^(?:(\w+)::)?(?:(\w+)::)?(\w+)$'
    match = re.match(pattern, volume_name)
    if match:
        realm, pod, volume = match.groups()
        return {
            'realm': realm,
            'pod': pod,
            'volume': volume
        }
    else:
        return None

# get the tag value for any tagging_rule
def get_tag_value(tag_by, container_name):
    if tag_by in TAGGING_RULES and container_name in TAGGING_RULES[tag_by]:
        return TAGGING_RULES[tag_by][container_name]
    return None

def tag_volume(fleet_member,volume,namespace, key,value):
    tags = [
        {"namespace": namespace, "key": key, "value": value}
    ]
    # See if there are any of the tags we are adding already on the volume        
    response = client.get_volumes_tags(context_names=fleet_member.member.name, resource_names=volume.name, namespaces=namespace)
    # Check the response
    if response.status_code != 200:
        # The tag check didn't work
        print(f"Failed to retrieve tags from {volume.name}. Status code: {response.status_code}, Error: {response.errors}")
        return
    else:
        # Remove the existing chargeback tag
        response = client.delete_volumes_tags(context_names=fleet_member.member.name, resource_names=volume.name, namespaces=namespace, keys=key)
        # Check the response
        if response.status_code == 200:
            if debug >=2:
                print(f"Tags removed successfully to volume {fleet_member.member.name},{volume.name},{tags}.")
        else:
            print(f"Couldn't remove tags from volume {fleet_member.member.name},{volume.name},{tags}.")
    # Add the chargeback tag
    response = client.put_volumes_tags_batch(context_names=fleet_member.member.name, resource_names=volume.name, tag=tags)
    # Check the response
    if response.status_code == 200:
        if debug >=2:
            print(f"Tags added successfully to volume {fleet_member.member.name},{volume.name},{tags}.")
    else:
        print(f"Failed to add tags to {fleet_member.member.name},{volume.name},{tags}. Status code: {response.status_code}, Error: {response.errors}")
    
    if (debug >= 3): 
        print(f"{namespace},{array_name},{volume.name},{volume.space.total_provisioned},{volume.space.total_used},{volume.space.snapshots}")
    

# Go through all volumes on this host and tag the volumes according to the tagging plan
def process_volumes(fleet_member):
    response = client.get_volumes(context_names=fleet_member.member.name)
    if response.status_code == 200:
            if debug >1:
                print(f"finding volumes for array {fleet_member.member.name}")
            volumes=response.items
    else:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")
        return()
    
    for volume in volumes:
        result = match_volume_name(volume.name)
        
        vols_realm = result.get("realm")
        vols_pod = result.get("pod")

        if vols_realm:
            tag_by = 'realm'
            tag_value = get_tag_value(tag_by, vols_realm)
            if tag_value and debug >=2:
                print(f'Tag value for {tag_by} {vols_realm}: {tag_value}')
            elif debug >=2:
                print(f'No tagging rule found for {tag_by} {container_name}')
        elif vols_pod:
            tag_by = 'pod'
            tag_value = get_tag_value(tag_by, vols_pod)
            if tag_value and debug >=2:
                print(f'Tag value for {tag_by} {vols_pod}: {tag_value}')
            elif debug >=2:
                print(f'No tagging rule found for {tag_by} {vols_pod}')
        else:
            tag_value = get_tag_value("default","default")
    
        if debug >=1:
            print(f"Tagging array {fleet_member.member.name} volume {volume.name}, in namespace {NAMESPACE} with tag {TAG_KEY}: {tag_value}")

        tag_volume(fleet_member,volume,NAMESPACE,TAG_KEY,tag_value)
                            

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
                        print(f'User {USER_NAME} does not have admin privileges.')
                        return True
        else:
            print(f'Failed to get admins: {response.errors}')
    except PureError as e:
        print(f'Error checking admin level: {e}')

USER_NAME=""
TAG_API_TOKEN=""
FUSION_SERVER=""
NAMESPACE=""
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
    USER_NAME = global_variables.get('USER_NAME', '')
    API_TOKEN = global_variables.get('API_TOKEN', '')
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')
    TAG_KEY = "chargeback"

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
        
    # Get the arrays for reporting contexts for the nominated fleet
    for member in list_fleets():
        # Go over all members of the fleet
        if debug >= 3:
            print(f"Tag,Array,Volume,Allocated,Used,Snapshots")
        process_volumes(member)