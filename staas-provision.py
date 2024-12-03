import pandas as pd
from purestorage import Client, PureError

# Function to check if a realm exists
def realm_exists(client, realm_name):
    try:
        realms = client.list_realms()
        return any(realm['name'] == realm_name for realm in realms)
    except PureError as e:
        print(f"Error checking if realm {realm_name} exists: {e}")
        return False

# Function to create a realm
def create_realm(client, realm_name):
    try:
        response = client.create_realm(name=realm_name)
        if isinstance(response, PureError):
            print(f"Error creating realm {realm_name}: {response}")
        else:
            print(f"Realm {realm_name} created successfully")
    except PureError as e:
        print(f"Error creating realm {realm_name}: {e}")

# Function to check if a workload exists
def workload_exists(client, workload_name):
    try:
        workloads = client.list_workloads()
        return any(workload['name'] == workload_name for workload in workloads)
    except PureError as e:
        print(f"Error checking if workload {workload_name} exists: {e}")
        return False

# Function to create a workload
def create_workload(client, workload_name):
    try:
        response = client.create_workload(name=workload_name)
        if isinstance(response, PureError):
            print(f"Error creating workload {workload_name}: {response}")
        else:
            print(f"Workload {workload_name} created successfully")
    except PureError as e:
        print(f"Error creating workload {workload_name}: {e}")

# Function to create volumes
def create_volumes(client, realm_name, workload_name, num_volumes, size_volumes):
    for i in range(num_volumes):
        volume_name = f"{realm_name}::{workload_name}::volume{i+1}"
        try:
            response = client.create_volume(name=volume_name, size=size_volumes)
            if isinstance(response, PureError):
                print(f"Error creating volume {volume_name}: {response}")
            else:
                print(f"Volume {volume_name} created successfully")
        except PureError as e:
            print(f"Error creating volume {volume_name}: {e}")

# Function to create hosts
def create_hosts(client, host_name, workload_name):
    try:
        response = client.create_host(name=host_name)
        if isinstance(response, PureError):
            print(f"Error creating host {host_name}: {response}")
        else:
            print(f"Host {host_name} created successfully")
            # Connect host to workload
            response = client.connect_host_to_workload(host_name=host_name, workload_name=workload_name)
            if isinstance(response, PureError):
                print(f"Error connecting host {host_name} to workload {workload_name}: {response}")
            else:
                print(f"Host {host_name} connected to workload {workload_name} successfully")
    except PureError as e:
        print(f"Error creating host {host_name}: {e}")

# Main script
if __name__ == "__main__":
    try:
        # Initialize the client
        client = Client(FUSION_API_URL, api_token=API_TOKEN)

        # Read the spreadsheet
        spreadsheet = pd.ExcelFile('Realms_Config.xlsx')

        # Process realms and workloads
        realms_workloads_df = spreadsheet.parse('Realms_Workloads')
        for index, row in realms_workloads_df.iterrows():
            realm_name = row['realm']
            workload_name = row['workload']
            num_volumes = row['number_of_volumes']
            size_volumes = row['size_of_volumes']

            # Check if the realm exists
            if not realm_exists(client, realm_name):
                # Create the realm if it does not exist
                create_realm(client, realm_name)
            else:
                print(f"Realm {realm_name} already exists.")

            # Check if the workload exists
            if not workload_exists(client, workload_name):
                # Create the workload if it does not exist
                create_workload(client, workload_name)
            else:
                print(f"Workload {workload_name} already exists.")

            # Create volumes
            create_volumes(client, realm_name, workload_name, num_volumes, size_volumes)

        # Process hosts and workloads
        hosts_workloads_df = spreadsheet.parse('Hosts_Workloads')
        for index, row in hosts_workloads_df.iterrows():
            host_name = row['host']
            workload_name = row['workload']

            # Create hosts and connect to workloads
            create_hosts(client, host_name, workload_name)

    except PureError as e:
        print(f"Error initializing client: {e}")