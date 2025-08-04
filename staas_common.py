
import argparse
import logging
from typing import List, Optional, Any
from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError

DEBUG_LEVEL = 0
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
if DEBUG_LEVEL > 0:
    logger.setLevel(logging.DEBUG)


"""
staas_common.py
---------------
Shared utility functions for STAAS-Reporting-Fusion scripts.
Includes argument parsing, Fusion client setup, API helpers, and fleet/member listing.
"""

from pypureclient import flasharray
from pypureclient.flasharray import Client, PureError


def parse_arguments(options: str) -> argparse.Namespace:
    """
    Parse command-line arguments for the reporting/tagging scripts.
    Args:
        options: 'report' or 'tag_vols' to determine which arguments to expect
    Returns:
        argparse.Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser(description='STAAS Reporting Scripts')
    parser.add_argument('--config', type=str, required=True, help='Complete path to filename of the configuration file')
    if options == "report":
        parser.add_argument('--reportdir', type=str, required=True, help='Directory for the reporting files')
    try:
        return parser.parse_args()
    except SystemExit as e:
        logger.error(f"Error parsing arguments: {e}")
        raise


def initialise_client(fusion_server: str, user_name: str, api_token: str) -> Optional[Client]:
    """
    Initialize and return a Fusion API client.
    Args:
        fusion_server: Fusion server address
        user_name: Username for authentication
        api_token: API token for authentication
    Returns:
        flasharray.Client instance or None on failure
    """
    try:
        client = flasharray.Client(target=fusion_server, username=user_name, api_token=api_token)
        return client
    except PureError as e:
        logger.error(f"Failed to initialize client: {e}")
        return None


def check_purity_role(client: Client, user_name: str) -> str:
    """
    Placeholder for checking the user's role on the array. Returns 'array_admin' by default.
    """
    # TODO: Implement actual role check if API supports it
    return "array_admin"


def check_api_version(client: Client, min_version: float) -> bool:
    """
    Check if the Fusion API version meets the minimum required version.
    Args:
        client: Fusion API client
        min_version: Minimum version as float
    Returns:
        True if version is sufficient, False otherwise
    """
    try:
        version = float(client.get_rest_version())
        if version >= min_version:
            return True
        else:
            logger.warning(f"API version {version} is less than the minimum required version {min_version}")
            return False
    except PureError as e:
        logger.error(f"Failed to check API version: {e}")
        return False


def list_fleets(client: Client) -> List[str]:
    """
    List all fleets visible to the Fusion client.
    Args:
        client: Fusion API client
    Returns:
        List of fleet names
    """
    try:
        response = client.get_fleets()
        if response.status_code == 200:
            fleets = response.items
            fleet_names = [fleet.name for fleet in fleets]
            return fleet_names
        else:
            logger.error(f"Failed to retrieve fleets. Status code: {response.status_code}, Error: {response.errors}")
            return []
    except PureError as e:
        logger.error(f"Exception when calling get_fleets: {e}")
        return []


def list_members(client: Client, fleets: List[str]) -> List[str]:
    """
    List all members (arrays) for the given fleets.
    Args:
        client: Fusion API client
        fleets: List of fleet names
    Returns:
        List of member (array) names
    """
    all_members: List[str] = []
    for fleet in fleets:
        try:
            response = client.get_fleets_members()
            if response.status_code == 200:
                members = list(response.items)
                member_names = [member.member.name for member in members]
                all_members.extend(member_names)
            else:
                logger.error(f"Failed to list members. Status code: {response.status_code}, Error: {response.errors}")
                return []
        except PureError as e:
            logger.error(f"Failed to list members: {e}")
            return []
    return all_members