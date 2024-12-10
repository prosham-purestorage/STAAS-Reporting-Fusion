import pandas as pd
import pypureclient
import urllib3

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

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

        # Get all volumes on the array
        volumes = list(client.get_volumes().items)
        tags = [
            {"key": "chargeback", "value": "App1", "namespace": "Telstra-STAAS"},
        ]
        # Read the spreadsheet
        spreadsheet = pd.ExcelFile('STAAS_Provisioning.xlsx')
        # Process each app
        pods_apps_df = spreadsheet.parse('Pods_Apps')
        for index, row in pods_apps_df.iterrows():
            array_name=row['arrays']
            pod_name = row['pod']
            app_name = row['app']
            num_volumes = row['number_of_volumes']
            size_volumes = row['size_of_volumes']

            # Check if the pod exists
            response = client.get_pods(names=[pod_name], context=array_name)
            if not response.items:
                pod_data = flasharray.PodPost(name=pod_name)
                client.post_pods(pod_data, context=array_name)
            else:
                print(f"Pod {pod_name} already exists on array {array_name}.")

            # Create volumes
            #create_volumes(client, array_name, app_name, num_volumes, size_volumes)

    except PureError as e:
        print(f"Error initializing client: {e}")