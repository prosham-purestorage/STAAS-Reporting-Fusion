import pandas as pd
import pypureclient
import urllib3

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

debug=1

# Function to create and tag volumes
def create_volumes(client, arrays_name, app_name, num_volumes, size_volumes):
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

#def tag_volumes(volumes,tags):



def list_arrays(client):
    # Retrieve the list of FlashArrays in the fleet
    response = client.get_fleets()
    # Check the response
    if response.status_code == 200:
        fleets = response.items
        for fleet in fleets:
            if debug>0:
                print(f"Fleet Name: {fleet.name}")

            for member in fleet.members:
                print(f"  Array Name: {member.name}, Array ID: {member.id}")
            else:
        print(f"Failed to retrieve fleets. Status code: {response.status_code}, Error: {response.errors}")
    return fleets

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
        # Get the arrays for reporting contexts
        arrays=list_arrays(client)
        # Get all volumes on the array
        volumes = list(client.get_volumes(context=arrays).items)
        if debug>0 print(f{Found volumes {volumes}})
        tags = [
            {"key": "chargeback", "value": "App1", "namespace": "Telstra-STAAS"},
        ]
        # Tag all volumes
        #tag_volumes(volumes,tags)

    except PureError as e:
        print(f"Error initializing client: {e}")