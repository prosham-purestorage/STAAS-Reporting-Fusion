<<<<<<< HEAD
# STAAS-Reporting-Fusion

This software can be used to add chargeback reporting to an MSP or Enterprise Storage environment with Pure Storage Arrays.

This package adds chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays and provides regular space reporting for chargeback.

# Roadmap
- **FlashBlade is not supported at this time (Fusion support on FlashBlade has been released, for FlashBlade//S and //E on 4.5.6, but no tagging - Directory reporting is on the current roadma p for this package)
- **Filesystems/Directories are being at this time (not possible to report with Fusion yet, or tag them)
- **FOCUS Rating output is a future consideration. See [https://focus.finops.org/what-is-focus/]
- **API Versioning to aid in change control

## Dependencies and Installation

- **Purity//FA Rest API**: Minimum version 2.42 (Purity//FA 6.8.5 and above) to access the Fusion API.
- **py-pure-client Python SDK**: Minimum version 1.66.0, which includes support for the required API calls. See [py-pure-client](https://github.com/PureStorage-OpenConnect/py-pure-client).

## Runtime Requirements

The scripts require the following arguments:
- `--config` (both scripts - location of a configuration spreadsheet)
- `--report` (folder for output reports, only for `staas-reporting.py`)

The Username and API Token must be stored in environment variables for the user running the script:
- `PURE_USER_NAME`
- `PURE_API_TOKEN`

These credentials must have array admin levels on all fleet members to run the tagging portion and read access for reporting.

For security reasons, two different IDs can be used for the reporting server OS and Purity access level to separate the permissions for tagging volumes and generating reporting spreadsheets.

Configuration data is retrieved from the spreadsheet `STAAS_Tagging.xlsx`, in the worksheet named `Fleet` (example provided - customize for your site).

The `FUSION_SERVER` is the DNS entry for a server that is a member of the fleet on which you are reporting. For reliability, it can be a DNS round-robin entry of more than one of the Management IP addresses of the fleet members. The `NAMESPACE` entry in the configuration is used to store the chargeback metadata entries for each volume. These are retrieved at run-time.

### Tagging

The worksheet named `Fleet` defines the Fusion server entry point URL, and the Namespace to put user-defined tags into.

The worksheet named `Tagging_map` contains the rules for the tagging process, which will place tagging records on each matching volume by:
-`default` (the default chargeback tag)
-`realm`
-`pod`
-`workload`
-`hostgroup`

These are in decreasing order of precedence - the first match on a volume wins the tag for that container.

The script `staas-tag_vols.py` will connect to a server in the fleet and, for each member of the fleet, retrieve the volumes and apply a tag called `chargeback` in the namespace `NAMESPACE`, giving it a value based on the container (realm, pod, hostgroup, or host) defined in the tagging rules spreadsheet. If there are no matches, a default value should be defined in the `Tagging_rules` worksheet and will be applied.

An example spreadsheet is supplied, customise to your own requirements
### Reporting

Reporting spreadsheets are created in the reporting directory if they do no exist. Each time the reporting script is run, it will append timestamped records to the appropriate worksheet

The script `staas-reporting.py` will connect to the fleet and generate (or append to) a spreadsheets named:
-`Space_Report-Volumes-YYYY-MM.xlsx`
-`Space_Report-Directories-YYYY-MM.xlsx`

The Volume Reporting script has one worksheet per chargeback code.
The records on each sheet are date/time stamped so that space can be rated externally over time.
The records contain the space details for each volume

The Directories Reporting script has one worksheet per array.
The records on each sheet are date/time stamped so that space can be rated externally over time.
The records contain the space details for each managed directory

Headers are written to each sheet on the first pass only; subsequent script runs append records to each sheet. This allows the reporting to use the same report output each month for ease of processing with pivot tables, for example.
=======
# STAAS-Reporting-Fusion

This package adds chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays and provides regular space reporting for chargeback.
FlashBlade is not supported at this time (Fusion support on FlashBlade has been released, for FlashBlade//S and //E on 4.5.6, but no tagging - Directory reporting is on the current roadma p for this package)
Filesystems/Directory are not reported at this time (not possible to report with Fusion yet, or tag them)
Realms are not supported at this time (awaiting Fusion support for Realms)

## Dependencies and Installation

- **Purity//FA Rest API**: Minimum version 2.42 (Purity//FA 6.8.5 and above) to access the Fusion API.
- **py-pure-client Python SDK**: Minimum version 1.66.0, which includes support for the required API calls. See [py-pure-client](https://github.com/PureStorage-OpenConnect/py-pure-client).

## Runtime Requirements

The scripts require the following arguments:
- `--config` (both scripts - location of a configuration spreadsheet)
- `--report` (folder for output reports, only for `staas-reporting.py`)

The Username and API Token must be stored in environment variables for the user running the script:
- `PURE_USER_NAME`
- `PURE_API_TOKEN`

These credentials must have array admin levels on all fleet members to run the tagging portion and read access for reporting.

For security reasons, two different IDs can be used for the reporting server OS and Purity access level to separate the permissions for tagging volumes and generating reporting spreadsheets.

Configuration data is retrieved from the spreadsheet `STAAS_Tagging.xlsx`, in the worksheet named `Fleet` (example provided - customize for your site).

The `FUSION_SERVER` is the DNS entry for a server that is a member of the fleet on which you are reporting. For reliability, it can be a DNS round-robin entry of more than one of the Management IP addresses of the fleet members. The `NAMESPACE` entry in the configuration is used to store the chargeback metadata entries for each volume. These are retrieved at run-time.

### Tagging

The worksheet named `Fleet` defines the Fusion server entry point URL, and the Namespace to put user-defined tags into.

The worksheet named `Tagging_map` contains the rules for the tagging process, which will place tagging records on each matching volume by:
-`default` (the default chargeback tag)
-`realm`
-`pod`
-`workload`
-`hostgroup`

These are in decreasing order of precedence - the first match on a volume wins the tag for that container.

The script `staas-tag_vols.py` will connect to a server in the fleet and, for each member of the fleet, retrieve the volumes and apply a tag called `chargeback` in the namespace `NAMESPACE`, giving it a value based on the container (realm, pod, hostgroup, or host) defined in the tagging rules spreadsheet. If there are no matches, a default value should be defined in the `Tagging_rules` worksheet and will be applied.

An example spreadsheet is supplied, customise to your own requirements
### Reporting

Reporting spreadsheets are created in the reporting directory if they do no exist. Each time the reporting script is run, it will append timestamped records to the appropriate worksheet

The script `staas-reporting.py` will connect to the fleet and generate (or append to) a spreadsheets named:
-`Space_Report-Volumes-YYYY-MM.xlsx`
-`Space_Report-Directories-YYYY-MM.xlsx`

The Volume Reporting script has one worksheet per chargeback code.

---

## Script Overviews


### staas-tag_vols.py

Tags block volumes in a Pure Storage Fusion fleet for chargeback, based on rules in a spreadsheet. Tagging is prioritized by realm, pod, workload, host group, host, and default.

**Usage Example:**

```sh
python staas-tag_vols.py --config config/STAAS_Config.xlsx
```

### staas-reporting.py

Generates space usage reports for volumes and directories, grouped by chargeback tag, and writes them to Excel files.

**Usage Example:**

```sh
python staas-reporting.py --config config/STAAS_Config.xlsx --reportdir reports/
```

---


## Configuration Spreadsheet Format

The configuration Excel file (e.g., `STAAS_Config.xlsx`) must contain at least two worksheets:

- **Fleet**: Contains global settings. Example columns:
  - `FUSION_SERVER`: DNS or IP of a Fusion fleet member
  - `NAMESPACE`: Namespace for tagging

- **Tagging_map**: Defines tagging rules. Example columns:
  - `Tag_By`: One of `realm`, `pod`, `workload`, `host_group`, `host`, `default`
  - `Container_Name`: Name of the realm/pod/etc. (or 'default')
  - `Tag_Value`: The value to assign for the chargeback tag

---

## Tagging Logic


When tagging, the script checks for a match in this order:

1. Realm
2. Pod
3. Workload
4. Host Group
5. Host
6. Default

The first match found is used for the tag value. If no match is found, the default is applied.

---

## Reporting Output


Reports are written to Excel files in the specified report directory:

- `Space-Report-Volumes-YYYY-MM.xlsx`: One worksheet per chargeback code, with space details for each volume.
- `Space-Report-Directories-YYYY-MM.xlsx`: One worksheet per array, with space details for each managed directory.

Each worksheet is appended to on each run, with date/time-stamped records for historical tracking.

---

## Example Environment Variables


Set these before running the scripts:

```sh
export PURE_USER_NAME=your_fusion_user
export PURE_API_TOKEN=your_fusion_api_token
```

---

## Additional Notes

- Both scripts require Python 3 and the dependencies listed in `requirements.txt`.
- Ensure you have write access to the report directory and the config file is accessible.
- For more details, see the docstrings and comments in each script.
The records on each sheet are date/time stamped so that space can be rated externally over time.
The records contain the space details for each volume

The Directories Reporting script has one worksheet per array.
The records on each sheet are date/time stamped so that space can be rated externally over time.
The records contain the space details for each managed directory

Headers are written to each sheet on the first pass only; subsequent script runs append records to each sheet. This allows the reporting to use the same report output each month for ease of processing with pivot tables, for example.
>>>>>>> 1ca6b66 (Clean up environment: update .gitignore, VSCode settings, requirements, and reporting scripts)
