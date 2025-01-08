# STAAS-Reporting-Fusion

This package will add chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays, and then provide regular space reporting for chargeback.


## Dependancies and Installation

It depends on some external packages:

    pip install pandas
    pip install openpyxl
    pip install py-pure-client

The minimum Purity//FA Rest API version is 2.39, so that the Fusion API is available (Purity//FA 6.8.2 and above)
The minimum py-pure-client Python SDK is 1.60, that includes Python support for the required API calls - see <https://github.com/PureStorage-OpenConnect/py-pure-client>

## Runtime 

### Tagging and Reporting Processes
The Username and API Token to run the script must be stored in environment variables
    PURE_USER_NAME
    PURE_API_TOKEN

These credentials must have array admin levels on all fleet members to be able to run the tagging portion, and read access to be able to perform reporting.

For security reasons, two different IDs can be used for the reporting server OS and Purity access level, to separate the permissions for tagging volumes and then generating reporting spreadsheets.
 
Configuration data is retrieved from the spreadsheet 'STAAS_Tagging.xlsx', in the worksheet named 'Fleet' (example provided - customise for your site)

The FUSION_SERVER is the DNS entry for a server that is a member of the fleet on which you are reporting. For reliability, it can be a DNS round robin entry of more than one of the Management IP addresses of the fleet members.
The NAMESPACE antry in thr is used to store the chargeback metadata entries for each volume.
These are retrieved at run-time.

### Tagging
The worksheet named 'Tagging_map' contains the rules for the tagging process, that will place tagging records on each matching volume by:
    realm
    pod
    hostgroup (not yet implemented)
    host (not yet implemented)

These are in decreasing order of precedence - the first match on a volume wins the tag for that container.
The script 'staas-tag.vols.py' will connect to a server in the fleet, and for each member of the fleet, retrieve the volumes and apply a tag called 'chargeback' in the namespace NAMESPACE, and give it a value based on the container (realm, pod, hostgroup or host) defined in the tagging rules spreadsheet. If there are no matches, a default value should be defined in the Tagging_rules worksheet and that will be applied.
