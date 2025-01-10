import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

debug=2

def parse_arguments(options):
    import argparse
    parser = argparse.ArgumentParser(description='STAAS Reporting Scripts')
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file')
    if options == "report":
        parser.add_argument('--report', type=str, required=True, help='Path to the reporting file')
    try:
        return parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print(f"Error parsing arguments: {e}")
        import sys
        sys.exit(e.code)

def initialise_client(fusion_server, user_name, api_token):
    try:
        client = flasharray.Client(target=fusion_server, username=user_name, api_token=api_token)
        return client
    except PureError as e:
        print(f"Failed to initialize client: {e}")
        return None

def check_purity_role(client, user_name):
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