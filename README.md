# STAAS-Reporting-Fusion

This package adds chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays and provides regular space reporting for chargeback.

## Dependencies and Installation

- **Purity//FA Rest API**: Minimum version 2.39 (Purity//FA 6.8.2 and above) to access the Fusion API.
- **py-pure-client Python SDK**: Minimum version 1.61.0, which includes support for the required API calls. See [py-pure-client](https://github.com/PureStorage-OpenConnect/py-pure-client).

## Runtime Requirements

The scripts require the following arguments:
- `--config` (both scripts)
- `--report` (only for `staas-reporting.py`)

The Username and API Token must be stored in environment variables for the user running the script:
- `PURE_USER_NAME`
- `PURE_API_TOKEN`

These credentials must have array admin levels on all fleet members to run the tagging portion and read access for reporting.

For security reasons, two different IDs can be used for the reporting server OS and Purity access level to separate the permissions for tagging volumes and generating reporting spreadsheets.

Configuration data is retrieved from the spreadsheet `STAAS_Tagging.xlsx`, in the worksheet named `Fleet` (example provided - customize for your site).

The `FUSION_SERVER` is the DNS entry for a server that is a member of the fleet on which you are reporting. For reliability, it can be a DNS round-robin entry of more than one of the Management IP addresses of the fleet members. The `NAMESPACE` entry in the configuration is used to store the chargeback metadata entries for each volume. These are retrieved at run-time.

### Tagging

The worksheet named `Tagging_map` contains the rules for the tagging process, which will place tagging records on each matching volume by:
- realm
- pod
- hostgroup (not yet implemented)
- host (not yet implemented)

These are in decreasing order of precedence - the first match on a volume wins the tag for that container.

The script `staas-tag_vols.py` will connect to a server in the fleet and, for each member of the fleet, retrieve the volumes and apply a tag called `chargeback` in the namespace `NAMESPACE`, giving it a value based on the container (realm, pod, hostgroup, or host) defined in the tagging rules spreadsheet. If there are no matches, a default value should be defined in the `Tagging_rules` worksheet and will be applied.

### Reporting

The script `staas-reporting.py` will connect to the fleet and generate a spreadsheet with:
- A worksheet per detected chargeback tag value
- One worksheet for volumes that have no tag
- A fleet space report

The records on each sheet are date/time stamped so that space can be rated externally over time.

Headers are written to each sheet on the first pass only; subsequent script runs append records to each sheet. This allows the reporting to use the same report output each month for ease of processing with pivot tables, for example.