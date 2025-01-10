# This file is part of STAAS-Reporting-Fusion.
#
# STAAS-Reporting-Fusion is licensed under the BSD 2-Clause License.
# You may obtain a copy of the License at
#
#     https://opensource.org/licenses/BSD-2-Clause
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import pandas as pd
import urllib3
from datetime import datetime
from openpyxl import load_workbook
from staas_common import (
    parse_arguments,
    initialise_client,
#   check_purity_role,
    check_api_version,
    list_fleets
)


debug = 2

# Header rows for the reporting spreadsheet are defined here
VOLUME_HEADER_ROWS = [
    ['Date/Time', 'Array', 'Volume']
]

ARRAY_HEADER_ROWS = [
    ['Date/Time', 'Array']  # Initial headers, will be updated dynamically
]

# Disable certificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def report_volumes(client, fleet_member_name, namespace, tag_key):
    volume_set = []
    response = client.get_volumes(context_names=fleet_member_name)
    if response.status_code == 200:
        if debug >= 2:
            print(f"Finding volumes for array {fleet_member_name}")
        for volume in response.items:
            if volume.subtype == 'regular':
                volume_set.append(volume.name)
            else:
                if debug >= 4:
                    print(f'Non-regular volume {volume.name} found - not reporting it.')
        tags = read_volume_tags(client, fleet_member_name, volume_set, namespace, tag_key)
        space_values = get_volume_space(client, fleet_member_name, volume_set)
        volumes_by_tag = {}
        volumes_without_tag = []
        if space_values:
            first_space = next(iter(space_values.values()))
            headers = ['Date/Time', 'Array', 'Volume'] + list(first_space.keys())
            VOLUME_HEADER_ROWS[0] = headers
        for volume in volume_set:
            tag = tags.get(volume, 'No tag')
            space = space_values.get(volume, {})
            volume_info = {
                'Date/Time': NOW,
                'Array': fleet_member_name,
                'Volume': volume
            }
            for key in VOLUME_HEADER_ROWS[0][3:]:
                volume_info[key] = space.get(key, '')
            if tag == 'No tag':
                volumes_without_tag.append(volume_info)
            else:
                if tag not in volumes_by_tag:
                    volumes_by_tag[tag] = []
                volumes_by_tag[tag].append(volume_info)
        return volumes_by_tag, volumes_without_tag
    else:
        print(f"Failed to retrieve volumes. Status code: {response.status_code}, Error: {response.errors}")
        return {}, []

def report_arrays(client, fleet_members):
    fleet_space_report = []
    for fleet_member in fleet_members:
        response = client.get_arrays_space(context_names=fleet_member.member.name)
        if response.status_code == 200:
            if debug >= 2:
                print(f"Space usage for array {fleet_member.member.name}")
            if response.items and hasattr(response.items[0], 'space'):
                space = response.items[0].space.__dict__
                space['Date/Time'] = NOW
                space['Array'] = fleet_member.member.name
                fleet_space_report.append(space)
            else:
                print(f"No space information available for array {fleet_member.member.name}")
        else:
            print(f"Failed to retrieve space usage. Status code: {response.status_code}, Error: {response.errors}")
    return fleet_space_report

# Main script
if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments("report")

    # Read the configuration file
    config_path = os.path.join(args.config)
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        exit(1)

    config_spreadsheet = pd.ExcelFile(config_path)

    # Read the Excel file
    fleet_df = config_spreadsheet.parse('Fleet')

    # Extract global variables from the Fleet sheet
    global_variables = fleet_df.iloc[0].to_dict()

    # Assign global variables
    USER_NAME = os.getenv('PURE_USER_NAME')
    API_TOKEN = os.getenv('PURE_API_TOKEN')
    FUSION_SERVER = global_variables.get('FUSION_SERVER', '')
    NAMESPACE = global_variables.get('NAMESPACE', '')
    TAG_KEY = "chargeback"

    NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

    client = initialise_client(FUSION_SERVER, USER_NAME, API_TOKEN)
    if not client:
        exit(1)
    #role = check_purity_role(client, USER_NAME) 
    # Check to see minimum version of 2.39 & array admin privileges for this user
    #if not (role == "array_admin" or role == "read_only)"):
    #   exit(1)
    if not check_api_version(client, 2.39, debug):
        exit(2)

    # Get the arrays for reporting contexts for the nominated fleet
    all_volumes_by_tag = {}
    all_volumes_without_tag = []

    fleet_members = list_fleets(client)

    for fleet_member in fleet_members:
        volumes_by_tag, volumes_without_tag = report_volumes(client, fleet_member.member.name, NAMESPACE, TAG_KEY)
        for tag, volumes in volumes_by_tag.items():
            if tag not in all_volumes_by_tag:
                all_volumes_by_tag[tag] = []
            all_volumes_by_tag[tag].extend(volumes)
        all_volumes_without_tag.extend(volumes_without_tag)

    # Collect space data for the arrays
    fleet_space_report = report_arrays(client, fleet_members)

    # Update ARRAY_HEADER_ROWS dynamically
    if fleet_space_report and len(ARRAY_HEADER_ROWS) == 1:
        ARRAY_HEADER_ROWS[0].extend(fleet_space_report[0].keys())

    # Create or append to the reporting spreadsheet
    report_path = os.path.join(args.report)
    try:
        if os.path.exists(report_path):
            try:
                book = load_workbook(report_path)
                with pd.ExcelWriter(report_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    for tag, volumes in all_volumes_by_tag.items():
                        df = pd.DataFrame(volumes)
                        sheet_name = f"Chargeback {tag}"
                        if sheet_name in book.sheetnames:
                            startrow = book[sheet_name].max_row
                            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=startrow)
                        else:
                            df.to_excel(writer, sheet_name=sheet_name, index=False, header=VOLUME_HEADER_ROWS[0])
                    if all_volumes_without_tag:
                        df = pd.DataFrame(all_volumes_without_tag)
                        if 'No Tag' in book.sheetnames:
                            startrow = book['No Tag'].max_row
                            df.to_excel(writer, sheet_name='No Tag', index=False, header=False, startrow=startrow)
                        else:
                            df.to_excel(writer, sheet_name='No Tag', index=False, header=VOLUME_HEADER_ROWS[0])
                    # Write the fleet space report
                    if fleet_space_report:
                        df = pd.DataFrame(fleet_space_report)
                        if 'Fleet Space Report' in book.sheetnames:
                            startrow = book['Fleet Space Report'].max_row
                            df.to_excel(writer, sheet_name='Fleet Space Report', index=False, header=False, startrow=startrow)
                        else:
                            df.to_excel(writer, sheet_name='Fleet Space Report', index=False, header=ARRAY_HEADER_ROWS[0])
            except KeyError as e:
                print(f"KeyError: {e}. The file might be corrupted. Creating a new file.")
                with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                    for tag, volumes in all_volumes_by_tag.items():
                        df = pd.DataFrame(volumes)
                        df.to_excel(writer, sheet_name=f"Chargeback {tag}", index=False, header=VOLUME_HEADER_ROWS[0])
                    if all_volumes_without_tag:
                        df = pd.DataFrame(all_volumes_without_tag)
                        df.to_excel(writer, sheet_name='No Tag', index=False, header=VOLUME_HEADER_ROWS[0])
                    # Write the fleet space report
                    if fleet_space_report:
                        df = pd.DataFrame(fleet_space_report)
                        df.to_excel(writer, sheet_name='Fleet Space Report', index=False, header=ARRAY_HEADER_ROWS[0])
        else:
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                for tag, volumes in all_volumes_by_tag.items():
                    df = pd.DataFrame(volumes)
                    df.to_excel(writer, sheet_name=f"Chargeback {tag}", index=False, header=VOLUME_HEADER_ROWS[0])
                if all_volumes_without_tag:
                    df = pd.DataFrame(all_volumes_without_tag)
                    df.to_excel(writer, sheet_name='No Tag', index=False, header=VOLUME_HEADER_ROWS[0])
                # Write the fleet space report
                if fleet_space_report:
                    df = pd.DataFrame(fleet_space_report)
                    df.to_excel(writer, sheet_name='Fleet Space Report', index=False, header=ARRAY_HEADER_ROWS[0])
    except PermissionError as e:
        print(f"PermissionError: {e}. Please ensure the file is not open in another application.")