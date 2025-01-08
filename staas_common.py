# filepath: staas-common.py
# This file is part of STAAS-Reporting-Fusion.
#
# STAAS-Reporting-Fusion is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# STAAS-Reporting-Fusion is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with STAAS

import os
import pandas as pd
import pypureclient
import urllib3
import re
import pprint as pp

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError


# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# get a list of fleets from this array
def list_fleets(client):
    # Retrieve the list of fleets, then find all of the FlashArrays and volumes associated with the fleet
    response = client.get_fleets_members()
    if response.status_code == 200:
        fleets_members=response.items
    else:
        print(f"Failed to retrieve fleets/members. Status code: {response.status_code}, Error: {response.errors}")
    return(fleets_members)

# Check API version
def check_api_version(client, level, debug=1):
    version = client.get_rest_version()
    
    if float(version) >= level:
        return True
    else:
        if debug >= 1:
            print(f'API Version: {version}')
            print(f"API version needs to support Fusion v{level} at a minimum.")
        return False

# check if the user has the correct permissions (array_admin for tagging, or lesser read/readonly role for reporting)
def check_purity_role(client, USER_NAME, debug=1):
    try:
        response = client.get_admins()
        if response.status_code == 200:
            return "array_admin"
        elif response.status_code == 400:
            print(f'Failed to get admins: {response.errors}')
            return "readonly"
    except PureError as e:
        print(f'Error checking admin level: {e}')
    return False

# make the initial connection to the Fusion server
def initialise_client(FUSION_SERVER, USER_NAME, API_TOKEN):
    if not FUSION_SERVER:
        print("Fusion server not set.")
        return None
    if not USER_NAME:
        print("User name not set.")
        return None
    if not API_TOKEN: 
        print("API token not set.")
        return None
    try:
        client = Client(FUSION_SERVER, username=USER_NAME, api_token=API_TOKEN)
        return client
    except PureError as e:
        print(f"Error initializing client: {e}")
        return None