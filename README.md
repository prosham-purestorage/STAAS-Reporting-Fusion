STAAS-Reporting-Fusion

This package will add chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays, and then provide regular space reporting for chargeback.

It depends on some external packages:

    pip install pandas
    pip install openpyxl
    pip install py-pure-client

The minimum Purity//FA Rest API version is 2.38 for the fusion API, with Purity//FA version 6.8.2
FA/Files will be supported in an upcoming version.
Purity//FB will be supported in an upcoming version.

Global Variables are stored in a setup spreadsheet 'STAAS-tagging.xlsx' which defines tagging pattersand fleet information (The API key will move to an
environment variable in an upcoming version).
