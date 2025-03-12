from ninjapy.client import NinjaRMMClient
import os
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

NINJA_CLIENT_ID = os.getenv("NINJA_CLIENT_ID")
NINJA_CLIENT_SECRET = os.getenv("NINJA_CLIENT_SECRET")
NINJA_TOKEN_URL = os.getenv("NINJA_TOKEN_URL")
NINJA_SCOPE = os.getenv("NINJA_SCOPE")
NINJA_API_BASE_URL = os.getenv("NINJA_API_BASE_URL")

ninja = NinjaRMMClient(
    client_id=NINJA_CLIENT_ID,
    client_secret=NINJA_CLIENT_SECRET,
    token_url=NINJA_TOKEN_URL,
    scope=NINJA_SCOPE
)

def retrieve_all_ips():

    ninja_data = ninja.get_devices_detailed(expand='organization,location')
    #ninja_clients = ninja.get_organizations()
    #ninja_locations = ninja.get_locations()

    # Normalize the data from Ninja API responses
    ninja_data_normalized = pd.json_normalize(ninja_data)
    # ninja_clients_normalized = pd.json_normalize(ninja_clients) 
    # ninja_locations_normalized = pd.json_normalize(ninja_locations)

    # ninja_data = pd.merge(ninja_devices_normalized, ninja_locations_normalized, left_on='locationId', right_on='id', how='left',suffixes=('', '_location'))
    # ninja_data = pd.merge(ninja_data, ninja_clients_normalized, left_on='organizationId', right_on='id', how='left',suffixes=('', '_client'))


    # Keep only specified columns from ninja_data
    ninja_data_normalized = ninja_data_normalized[['references.organization.name', 'references.location.name', 'publicIP']]
    # Drop rows with empty values
    ninja_data_normalized = ninja_data_normalized.dropna()
    # Group by client, location and IP and count occurrences
    ip_counts = ninja_data_normalized.groupby(['references.organization.name', 'references.location.name', 'publicIP']).size().reset_index(name='count')

    # Sort by client name and count for better readability
    ip_counts = ip_counts.sort_values(['references.organization.name', 'count'], ascending=[True, False])

    return ip_counts.to_dict(orient='records')

