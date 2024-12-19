STAAS-Reporting-Fusion

This package will add chargeback metadata to block volumes on a fleet of Pure Storage FlashArrays, and then provide regular space reporting for chargeback.

It depends on some external packages:
    pip install pandas
    pip install openpyxl
    pip install py-pure-client

The minimum Purity//FA Rest API version is 2.38 for the fusion API

API Tokens are stored with other Global Variables in the 