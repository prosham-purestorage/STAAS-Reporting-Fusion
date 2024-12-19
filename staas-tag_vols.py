import pandas as pd
import pypureclient
import urllib3
import re

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError
#from pypureclient.client_settings import get_client_versions


debug=2

# Find and tag all volumes, with a correct chargeback code if defined, or the default IT code otherwise
def process_volumes(fleet_member):
    response = client.get_volumes(context_names=fleet_member.member.name)
    if response.status_code == 200:
            if debug >1:
                print(f"finding volumes for array {fleet_member.member.name}")
            volumes=response.items
    else:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")
        return()
    if debug >= 2:
            print(f"Array,Realm,Volume,Pod")
    for volume in volumes:
        if debug >= 2: 
            print(f"{fleet_member.member.name},{volume.name},{volume.pod}")
        response = client.put_volumes_tags_batch(context_names=fleet_member.member.name, resource_names=volume.name, tag=tags)
        # Check the response
        if response.status_code == 200:
            if debug >=1:
                print(f"Tags added successfully to volume {volume.name}.")
        else:
            print(f"Failed to add tags to {volume.name}. Status code: {response.status_code}, Error: {response.errors}")


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

# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Main script
if __name__ == "__main__":
    # Read the Excel file
    spreadsheet = pd.ExcelFile('STAAS_Tagging.xlsx')

    # Parse the specific sheet
    fleet_df = spreadsheet.parse('Fleet')

    # Extract global variables
    global_variables = fleet_df.iloc[0].to_dict()

    # Assign global variables
    USER_NAME = global_variables.get('USER_NAME', '')
    API_TOKEN = global_variables.get('API_TOKEN', '')
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')

    try:
        # Initialize the client
        client = Client(FUSION_SERVER,username=USER_NAME, api_token=API_TOKEN)
        # Check to see minimum version of 2.38 & array admin privileges for this user
        if not check_admin_level("array_admin"):
            exit(1)
        if not check_api_version(2.38):
            exit(2)
        
        tags = [
            {"key": "chargeback", "value": "IT", "namespace": "NAMESPACE"},
        ]
        
        # Get the arrays for reporting contexts for the nominated fleet
        for member in list_fleets():
            # Tag all volumes in pods for arrays in the fleet
            process_volumes(member)

    except PureError as e:
        print(f"Error initializing client: {e}")