import pypureclient
import urllib3
import re
import pprint as pp

"""
staas_common.py
---------------
Shared utility functions for STAAS-Reporting-Fusion scripts.
Includes argument parsing, Fusion client setup, API helpers, and fleet/member listing.
"""

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

debug=0

def parse_arguments(options):
    """
    Parse command-line arguments for the reporting/tagging scripts.
    Args:
        options: 'report' or 'tag_vols' to determine which arguments to expect
    Returns:
        argparse.Namespace with parsed arguments
    """
    import argparse
    parser = argparse.ArgumentParser(description='STAAS Reporting Scripts')
    parser.add_argument('--config', type=str, required=True, help='Complete path to filename of the configuration file')
    if options == "report":
        parser.add_argument('--reportdir', type=str, required=True, help='Directory for the reporting files')
    try:
        return parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print(f"Error parsing arguments: {e}")
        import sys
        sys.exit(e.code)

def initialise_client(fusion_server, user_name, api_token):
    """
    Initialize and return a Fusion API client.
    Args:
        fusion_server: Fusion server address
        user_name: Username for authentication
        api_token: API token for authentication
    Returns:
        flasharray.Client instance or None on failure
    """
    try:
        client = flasharray.Client(target=fusion_server, username=user_name, api_token=api_token)
        return client
    except PureError as e:
        print(f"Failed to initialize client: {e}")
        return None

def check_purity_role(client, user_name):
    """
    Placeholder for checking the user's role on the array. Returns 'array_admin' by default.
    """
    # This code needs work - not sure how to do this
    return "array_admin"
    try:
        response = flasharray.AdminRole(name=user_name).get()
        if response.status_code == 200 and response.items:
            return response.items[0].role
        else:
            print(f"Failed to retrieve user role. Status code: {response.status_code}, Error: {response.errors}")
            return None
    except PureError as e:
        print(f"Failed to check purity role: {e}")
        return None

def check_api_version(client, min_version):
    """
    Check if the Fusion API version meets the minimum required version.
    Args:
        client: Fusion API client
        min_version: Minimum version as float
    Returns:
        True if version is sufficient, False otherwise
    """
    try:
        version = float(client.get_rest_version())
        if version >= min_version:
            return True
        else:
            if debug >= 1:
                print(f"API version {version} is less than the minimum required version {min_version}")
            return False
    except PureError as e:
        print(f"Failed to check API version: {e}")
        return False

def list_fleets(client):
    """
    List all fleets visible to the Fusion client.
    Args:
        client: Fusion API client
    Returns:
        List of fleet names
    """
    try:
        response = client.get_fleets()
        if response.status_code == 200:
            fleets = response.items
            fleet_names = [fleet.name for fleet in fleets]
            return fleet_names
        else:
            print(f"Failed to retrieve fleets. Status code: {response.status_code}, Error: {response.errors}")
            return []
    except PureError as e:
        print(f"Exception when calling get_fleets: {e}")
        return []

def list_members(client, fleets):
    """
    List all members (arrays) for the given fleets.
    Args:
        client: Fusion API client
        fleets: List of fleet names
    Returns:
        List of member (array) names
    """
    all_members = []
    for fleet in fleets:
        try:
            response = client.get_fleets_members()
            if response.status_code == 200:
                members = list(response.items)  # Convert ItemIterator to list
                # Print attributes of the first member to identify the correct attribute
                member_names = [member.member.name for member in members]  # Adjust attribute access
                all_members.extend(member_names)
            else:
                print(f"Failed to list members. Status code: {response.status_code}, Error: {response.errors}")
                return []
        except PureError as e:
            print(f"Failed to list members: {e}")
            return []
    return all_members