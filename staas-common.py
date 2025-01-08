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

# Check API version
def check_api_version(level):
    version = client.get_rest_version()
    
    if float(version) >= level:
        return True
    else:
        if debug >= 1:
            print(f'API Version: {version}')
            print(f"API version needs to support Fusion v{level} at a minimum.")
        return False

def check_admin_level(client, USER_NAME, desired_role, debug=0):
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
                        return False
        elif response.status_code == 400:
            print(f'Failed to get admins: {response.errors}')
            return False
    except PureError as e:
        print(f'Error checking admin level: {e}')
    return False

def initialize_client(FUSION_SERVER, USER_NAME, API_TOKEN):
    try:
        client = Client(FUSION_SERVER, username=USER_NAME, api_token=API_TOKEN)
        return client
    except PureError as e:
        print(f"Error initializing client: {e}")
        return None