import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp
from datetime import datetime

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError, Space


debug=1

def report_array(fleet_member):
    member_name = fleet_member.member.name
    # Get the tags on the volumes from the namespace        
    #response = Space(context_names=member_name)
    # Check the response
    if response.status_code != 200:
        # The tag check didn't work
        print(f"Failed to retrieve space from {member_name}. Status code: {response.status_code}, Error: {response.errors}")
        return
    else:
        pp.pprint(response.items)

# Go through all volumes on this host and create a spare report by volume with volume chargeback tags
def report_volumes(fleet_member):
    member_name = fleet_member.member.name
    dtnow = datetime.now().strftime("%Y-%m-%d %H:%M")
    # Get the tags on the volumes from the namespace        
    response = client.get_volumes_tags(context_names=member_name, namespaces=NAMESPACE)
    # Check the response
    if response.status_code != 200:
        # The tag check didn't work
        print(f"Failed to retrieve tags from {member_name}. Status code: {response.status_code}, Error: {response.errors}")
        return
    else:
        for tagged_volume in response.items:
            if (tagged_volume.namespace == NAMESPACE and tagged_volume.key == TAG_KEY):
                tag_set[tagged_volume.resource.name]=tagged_volume.value

    response = client.get_volumes(context_names=member_name)
    if response.status_code != 200:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")
        return
    else:
        if debug >=2:
            print(f"Finding volumes for array {member_name}")
        for volume in response.items:
            if volume.name in tag_set:
                print(f"{NAMESPACE},{member_name},{tag_set[volume.name]},{dtnow},{volume.name},{volume.space.total_provisioned},{volume.space.total_used},{volume.space.snapshots}")
            else:
                print(f"{NAMESPACE},{member_name},,{dtnow},{volume.name},{volume.space.total_provisioned},{volume.space.total_used},{volume.space.snapshots}")
        

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
tag_set={}

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
    for fleet_members in list_fleets():
        # Go over all members of the fleet
        #report_array(fleet_members)
        report_volumes(fleet_members)

    for 