import requests
import json

# Replace with your Fusion API endpoint and credentials
FUSION_API_URL = "https://fusion-api.example.com"
USERNAME = "your_username"
PASSWORD = "your_password"
REALM_NAME = "your_realm_name"  # Specify your realm name here
CHARGE_CODE = "your_charge_code"  # Specify your charge code here

# Function to get authentication token
def get_auth_token():
    url = f"{FUSION_API_URL}/auth/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["token"]

# Function to create a workload with tagged volumes
def create_workload(token, workload_name, storage_class, volumes, realm_name, charge_code):
    url = f"{FUSION_API_URL}/workloads"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Add tags to each volume
    for volume in volumes:
        volume["tags"] = [{"key": "charge_code", "value": charge_code}]
    
    payload = {
        "name": workload_name,
        "storage_class": storage_class,
        "volumes": volumes,
        "realm": realm_name  # Include the realm in the payload
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Main script
if __name__ == "__main__":
    try:
        # Get authentication token
        token = get_auth_token()

        # Define workload details
        workload_name = "example_workload"
        storage_class = "standard"
        volumes = [
            {"name": "volume1", "size": "100G"},
            {"name": "volume2", "size": "200G"}
        ]

        # Create workload with tagged volumes
        workload = create_workload(token, workload_name, storage_class, volumes, REALM_NAME, CHARGE_CODE)
        print("Workload created successfully:", workload)

    except requests.exceptions.RequestException as e:
        print("Error provisioning storage:", e)
