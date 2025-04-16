# STAAS-Reporting-Fusion

This package adds chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays and provides regular space reporting for chargeback.
FlashBlade is not supported at this time (Fusion support on FlashBlade has been released, for FlashBlade//S and //E on 4.5.6, but no tagging - Directory reporting is on the current roadma p for this package)
Filesystems/Directory are not reported at this time (not possible to report with Fusion yet, or tag them)
Realms are not supported at this time (awaiting Fusion support for Realms)

## Dependencies and Installation

- **Purity//FA Rest API**: Minimum version 2.41 (Purity//FA 6.8.5 and above) to access the Fusion API.
- **py-pure-client Python SDK**: Minimum version 1.65.0, which includes support for the required API calls. See [py-pure-client](https://github.com/PureStorage-OpenConnect/py-pure-client).

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

The Volume Reporting script has one worksheet per chargeback code.
The records on each sheet are date/time stamped so that space can be rated externally over time.
The records contain the space details for each volume

Headers are written to each sheet on the first pass only; subsequent script runs append records to each sheet. This allows the reporting to use the same report output each month for ease of processing with pivot tables, for example.
