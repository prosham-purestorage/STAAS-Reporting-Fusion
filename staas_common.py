import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

debug = 2

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

#def check_purity_role(client, user_name):
#    try:
#        response = client.get_users(names=[user_name])
#        if response.status_code == 200 and response.items:
#            return response.items[0].role
#        else:
#            print(f"Failed to retrieve user role. Status code: {response.status_code}, Error: {response.errors}")
#            return None
#    except PureError as e:
#        print(f"Failed to check purity role: {e}")
#        return None

def check_api_version(client, min_version, debug):
    try:
        response = client.get_arrays()
        if response.status_code == 200 and response.items:
            version = response.items[0].version
            if version >= min_version:
                return True
            else:
                if debug >= 1:
                    print(f"API version {version} is less than the minimum required version {min_version}")
                return False
        else:
            print(f"Failed to retrieve API version. Status code: {response.status_code}, Error: {response.errors}")
            return False
    except PureError as e:
        print(f"Failed to check API version: {e}")
        return False

def list_fleets(client):
    try:
        response = client.get_fleets()
        if response.status_code == 200:
            return response.items
        else:
            print(f"Failed to list fleets. Status code: {response.status_code}, Error: {response.errors}")
            return []
    except PureError as e:
        print(f"Failed to list fleets: {e}")
        return []
