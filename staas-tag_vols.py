import pandas as pd
import pypureclient
import urllib3

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError
from pypureclient.client_settings import get_client_versions


debug=1

# Function to find and tag volumes
def tag_volumes(client, arrays_name, app_name, num_volumes, size_volumes):
    for i in range(num_volumes):
        volume_name = f"{pod_name}::{workload_name}::volume{i+1}"
        
        
        try:
            response = client.create_volume(name=volume_name, size=size_volumes)
            if isinstance(response, PureError):
                print(f"Error creating volume {volume_name}: {response}")
            else:
                print(f"Volume {volume_name} created successfully")
        except PureError as e:
            print(f"Error creating volume {volume_name}: {e}")
                # Add the tag to the volumes using the correct method
        
        for volume in volumes:
            response = client.put_volumes_tags_batch(resources={volume.name}, tag=tags)
            # Check the response
            if response.status_code == 200:
                print(f"Tags added successfully to volume {volume.name}.")
            else:
                print(f"Failed to add tags to {volume.name}. Status code: {response.status_code}, Error: {response.errors}")




def list_fleets():
    # Retrieve the list of fleet, then find all of the FlashArrays and volumes associated with the fleet
    response = client.get_fleets_members()
    if response.status_code == 200:
        fleets_members=response.items
    else:
        print(f"Failed to retrieve fleets/members. Status code: {response.status_code}, Error: {response.errors}")
    return(fleets_members)

API_TOKEN="5887696c-bceb-1ea1-77df-f316fb18c090"
FUSION_SERVER="pstg-fa-02.mel.aulab.purestorage.com"
#FUSION_SERVER="10.111.0.5"
USER_NAME="prosham"

# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Main script
if __name__ == "__main__":
    try:
        # Initialize the client
        client = Client(FUSION_SERVER,username=USER_NAME, api_token=API_TOKEN)
        # Check to see minimum version of 2.37
        response = client.get_target_versions()
        # Check if the API version is at least 2.37
        #required_version = '2.37'
        #if api_version >= required_version:
        #    print(f"API version {api_version} is valid.")
        #else:
        #    raise ValueError(f"API version {api_version} is not supported. Minimum required version is {required_version}.")
        if response.status_code == 200:
            versions=response.items
        else:
            print(f"Failed to retrieve fleets/members. Status code: {response.status_code}, Error: {response.errors}")
        
        tags = [
            {"key": "chargeback", "value": "App1", "namespace": "Telstra-STAAS"},
        ]
        
        # Get the arrays for reporting contexts for the nominated fleet
        arrays=list_fleets()
        
        for array in arrays:
            print(f"Array {array.member.name} is in fleet {array.fleet.name}")
        # Tag all volumes
        #tag_volumes(volumes,tags)

    except PureError as e:
        print(f"Error initializing client: {e}")