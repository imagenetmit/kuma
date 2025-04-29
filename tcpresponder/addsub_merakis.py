from uptime_kuma_api import UptimeKumaApi,MonitorType
from ninjapy.client import NinjaRMMClient
import os
from dotenv import load_dotenv
import pandas as pd
import meraki
import sqlalchemy
import pymysql
load_dotenv()
NINJA_CLIENT_ID = os.getenv("NINJA_CLIENT_ID")
NINJA_CLIENT_SECRET = os.getenv("NINJA_CLIENT_SECRET")
NINJA_TOKEN_URL = os.getenv("NINJA_TOKEN_URL")
NINJA_SCOPE = os.getenv("NINJA_SCOPE")
NINJA_API_BASE_URL = os.getenv("NINJA_API_BASE_URL")
# UPTIME_KUMA_API_URL = os.getenv("UPTIME_KUMA_API_URL")\
UPTIME_KUMA_API_URL = "http://localhost:3003"
UPTIME_KUMA_USERNAME = os.getenv("UPTIME_KUMA_USERNAME")
UPTIME_KUMA_PASSWORD = os.getenv("UPTIME_KUMA_PASSWORD")
UPTIME_KUMA_DB_TYPE= os.getenv("UPTIME_KUMA_DB_TYPE")
UPTIME_KUMA_DB_HOSTNAME= os.getenv("UPTIME_KUMA_DB_HOSTNAME")
UPTIME_KUMA_DB_PORT= os.getenv("UPTIME_KUMA_DB_PORT")
UPTIME_KUMA_DB_NAME= os.getenv("UPTIME_KUMA_DB_NAME")
UPTIME_KUMA_DB_USERNAME= os.getenv("UPTIME_KUMA_DB_USERNAME")
UPTIME_KUMA_DB_PASSWORD= os.getenv("UPTIME_KUMA_DB_PASSWORD")

ninja = NinjaRMMClient(
    client_id=NINJA_CLIENT_ID,
    client_secret=NINJA_CLIENT_SECRET,
    token_url=NINJA_TOKEN_URL,
    scope=NINJA_SCOPE
)
meraki_api_key = os.getenv("MERAKI_API_KEY")

m = meraki.DashboardAPI(meraki_api_key, suppress_logging=True)
api = UptimeKumaApi(UPTIME_KUMA_API_URL)

orgs = m.organizations.getOrganizations()

# Create lists to store all organizations and networks
all_orgs = []
all_networks = []

# Collect all organizations
for org in orgs:
    all_orgs.append(org)
    # print(org["id"], org["name"])

# Collect networks from all organizations
for org in orgs:
    if org.get('samlConsumerUrl'):  
        try:
            # Get all networks for this organization
            networks = m.organizations.getOrganizationNetworks(org['id'])
            
            # Add networks to the combined list
            if networks:
                for network in networks:
                    all_networks.append({
                        'org_id': org.get('id'),
                        'org_name': org.get('name'),
                        'org_url': org.get('url'),
                        'network_id': network.get('id'),
                        'network_name': network.get('name'),
                        'network_url': network.get('url')
                    })
        except Exception as e:
            print(f"Error retrieving networks for {org['name']}: {str(e)}")

# Print summary
# print(f"\nTotal organizations: {len(all_orgs)}")
# print(f"Total networks: {len(all_networks)}")

all_networks_df = pd.json_normalize(all_networks)
# Create a list to store all device statuses
all_device_statuses = []

# Get device statuses from all organizations with samlConsumerUrl
for org in orgs:
    if org.get('samlConsumerUrl'):
        try:
            # Get all device statuses for this organization
            device_statuses = m.organizations.getOrganizationDevicesStatuses(org['id'])
            
            # Add device statuses to the combined list
            if device_statuses:
                for device in device_statuses:
                    all_device_statuses.append({
                        'org_id': org.get('id'),
                        'org_name': org.get('name'),
                        'device_name': device.get('name'),
                        'device_serial': device.get('serial'),
                        'device_mac': device.get('mac'),
                        'device_public_ip': device.get('publicIp'),
                        'device_network_id': device.get('networkId'),
                        'device_status': device.get('status'),
                        'device_last_reported': device.get('lastReportedAt'),
                        'device_product_type': device.get('productType'),
                        'device_model': device.get('model'),
                        'device_lan_ip': device.get('lanIp'),
                        'device_gateway': device.get('gateway'),
                        'device_ip_type': device.get('ipType'),
                        'device_primary_dns': device.get('primaryDns'),
                        'device_secondary_dns': device.get('secondaryDns'),
                        'device_configuration_updated': device.get('configurationUpdatedAt'),
                        'device_wan1_ip': device.get('wan1Ip'),
                        'device_wan1_gateway': device.get('wan1Gateway'),
                        'device_wan1_ip_type': device.get('wan1IpType'),
                        'device_wan1_primary_dns': device.get('wan1PrimaryDns'),
                        'device_wan1_secondary_dns': device.get('wan1SecondaryDns'),
                        'device_wan2_ip': device.get('wan2Ip'),
                        'device_wan2_gateway': device.get('wan2Gateway'),
                        'device_wan2_ip_type': device.get('wan2IpType'),
                        'device_wan2_primary_dns': device.get('wan2PrimaryDns'),
                        'device_wan2_secondary_dns': device.get('wan2SecondaryDns')
                    })
            
            # Print devices for debugging
            # for device in device_statuses:
                # print(device["serial"], device["name"])
                
        except Exception as e:
            print(f"Error retrieving device statuses for {org['name']}: {str(e)}")

# Print summary
# print(f"\nTotal devices across all organizations: {len(all_device_statuses)}")
 
# Get network_id and network_name columns from all_networks_df
# Make sure all_networks_df is a DataFrame and we're accessing columns correctly
try:
    m_locations = all_networks_df[['network_id', 'network_name','org_name']]
except KeyError as e:
    print(f"Error: Columns not found in DataFrame: {e}")
    # Check available columns
    print(f"Available columns: {all_networks_df.columns.tolist()}")
    m_locations = None

devices = ninja.get_devices_detailed(expand="organization,location")
devices_df = pd.json_normalize(devices)

ninja_orgs = ninja.get_organizations_detailed()
# Drop specified columns from ninja_orgs
for org in ninja_orgs:
    if 'settings' in org:
        org.pop('settings', None)
    if 'policies' in org:
        org.pop('policies', None)
    if 'description' in org:
        org.pop('description', None)
    if 'nodeApprovalMode' in org:
        org.pop('nodeApprovalMode', None)

ninja_orgs_df = pd.json_normalize(ninja_orgs)
ninja_orgs_exploded = ninja_orgs_df.explode('locations')
ninja_dict = ninja_orgs_exploded.to_dict(orient='records')
ninja_orgs_normalized = pd.json_normalize(ninja_dict)



from uptime_kuma_api import UptimeKumaApi,MonitorType
# api = UptimeKumaApi(UPTIME_KUMA_API_URL,timeout=30)

api = UptimeKumaApi(UPTIME_KUMA_API_URL,timeout=30)
api.login(os.getenv("UPTIME_KUMA_USERNAME"),os.getenv("UPTIME_KUMA_PASSWORD"))
kuma_monitors = api.get_monitors()
ping_monitors = [monitor for monitor in kuma_monitors if monitor['type'] == MonitorType.PING]
api_monitors = [monitor for monitor in kuma_monitors if monitor['type'] == MonitorType.JSON_QUERY]
active_orgs = [org for org in orgs if org.get('samlConsumerUrl') is not None]
kuma_monitors_df = pd.json_normalize(kuma_monitors) 
all_device_statuses_df = pd.json_normalize(all_device_statuses) 
orgs_df = pd.json_normalize(active_orgs) 

# Merge all_device_statuses_df and m_locations on network_id
if 'all_device_statuses_df' in locals() and m_locations is not None:
    # Check if device_network_id exists in all_device_statuses_df and network_id in m_locations
    if 'device_network_id' in all_device_statuses_df.columns and 'network_id' in m_locations.columns:
        # Perform the merge
        device_statuses_merged_df = pd.merge(
            all_device_statuses_df,
            m_locations,
            left_on='device_network_id',
            right_on='network_id',
            how='left'
        )
        

    else:
        print("Error: Required columns not found in one or both dataframes")
        print(f"all_device_statuses_df columns: {all_device_statuses_df.columns.tolist()}")
        print(f"m_locations columns: {m_locations.columns.tolist()}")
else:
    print("Error: One or both dataframes not available for merging")


# Compare organization names between all_device_statuses_df and orgs_df
# First, get unique organization names from both dataframes
status_org_names = orgs_df['name'].unique()
source_org_names = ninja_orgs_df['name'].unique()

# Check which names match and which don't
matching_names = []
non_matching_names = []

for org_name in status_org_names:
    if org_name in source_org_names:
        matching_names.append(org_name)
    else:
        non_matching_names.append(org_name)

# Display results
print(f"Total unique organization names in device statuses: {len(status_org_names)}")
print(f"Total unique organization names in orgs_df: {len(source_org_names)}")
print("\nMatching organization names:")
for name in matching_names:
    print(f"- {name}")

print("\nNon-matching organization names:")
for name in non_matching_names:
    print(f"- {name}")

# Calculate match percentage
match_percentage = (len(matching_names) / len(status_org_names)) * 100
print(f"\nMatch percentage: {match_percentage:.2f}%")


org_to_monitor_id = dict(zip(kuma_monitors_df['name'], kuma_monitors_df['id']))

# List to store results or responses from add_monitor calls
monitor_results = []

check_url = "https://api.meraki.com/api/v1/organizations/{org_id}/devices/statuses?serials[]={device_serial}"


# Create a new column in device_statuses_merged_df for 'check_url'
# This will format the URL with each row's org_id and device_serial
device_statuses_merged_df['check_url'] = device_statuses_merged_df.apply(
    lambda row: check_url.format(
        org_id=row.get('org_id', ''), 
        device_serial=row.get('device_serial', '')
    ),
    axis=1
)
# Create a new column in device_statuses_merged_df for 'headers'
# This will contain the headers needed for API requests

device_statuses_merged_df['headers'] = device_statuses_merged_df.apply(
    lambda row: {
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('MERAKI_API_KEY')}"
    },
    axis=1
)


excluded_orgs = [
        "CH Investment Partners",
        "ImageNet MIT Loaners",
        "CLONE THIS ORG",
        "Federman & Sherwood",
        "Dallas Institute of Humanities and Culture",
        "Laird Hammons Laird",
        "Tower Engineering Inc"
    ]
# Filter out devices from excluded organizations
device_statuses_merged_df = device_statuses_merged_df[~device_statuses_merged_df['org_name_x'].isin(excluded_orgs)]
device_statuses_merged_df = device_statuses_merged_df[device_statuses_merged_df['device_status']=="online"]
# Print the number of devices after filtering
print(f"Number of devices after filtering : {len(device_statuses_merged_df)}")

tags = api.get_tags()
monitors = api.get_monitors()
# Create a dictionary mapping tag names to device product types
tag_to_device_types = {}

for tag in tags:
    if tag['name'] == 'Firewall':
        tag_to_device_types[tag['id']] = ['appliance', 'cellularGateway']
    elif tag['name'] == 'Switch/AP':
        tag_to_device_types[tag['id']] = ['switch', 'wireless']
    elif tag['name'] == 'Meraki':
        tag_to_device_types[tag['id']] = ['appliance', 'cellularGateway', 'switch', 'wireless']
    else:
        # Default to empty list for other tags
        tag_to_device_types[tag['id']] = []

# Add device_product_type field to each tag
for tag in tags:
    tag['device_product_type'] = tag_to_device_types.get(tag['id'], [])
# Iterate through each row in merged_df

# Check for monitors that don't have a matching device in device_statuses_merged_df
# First, get all device serials from our merged dataframe
device_serials_in_df = set(device_statuses_merged_df['device_serial'].dropna().unique())

# Identify monitors that have a description matching a device serial but the device no longer exists
monitors_to_delete = []
for monitor in monitors:
    # Check if the monitor has a description that looks like a device serial
    monitor_description = monitor.get('description')
    # If description is blank, we know it is not a valid serial
    if not monitor_description:
        continue
        
    # Check if the description matches the expected serial number pattern (e.g., Q2KN-VAQP-E2NT)
    is_valid_serial = (isinstance(monitor_description, str) and 
                        len(monitor_description) == 14 and 
                        monitor_description[4] == '-' and 
                        monitor_description[9] == '-')
    
    if is_valid_serial and monitor_description not in device_serials_in_df:
        # This monitor's device serial doesn't exist in our current device list
        monitors_to_delete.append(monitor)
        

# Delete the identified monitors
for monitor in monitors_to_delete:
    try:
        api.delete_monitor(monitor['id'])
        print(f"Deleted monitor: {monitor['name']} (ID: {monitor['id']}) - Device serial: {monitor['description']}")
    except Exception as e:
        print(f"Failed to delete monitor {monitor['id']}: {str(e)}")

for index, row in device_statuses_merged_df.iterrows():

    # Check if a monitor already exists for this device serial
    device_serial = row.get('device_serial')
    if device_serial:
        # Check if any existing monitor has this device serial in its description
        monitor_exists = any(
            monitor.get('description') == device_serial and monitor.get('type') == MonitorType.PING
            for monitor in monitors
        )
        
        if monitor_exists:
            # Skip this device as it already has a monitor
            print("Skip device that already has a monitor.")
            continue

    
    # Check if org_name_x exists in the row and in the kuma_monitors_df
    org_name = row.get('org_name_x')
    dev_product_type = row.get('device_product_type')
    # Skip specific organizations

    if dev_product_type not in ['appliance']:
        continue
    if row.get('device_name'):
        device_name = f"{row.get('network_name')} {row.get('device_model')} {row.get('device_name')}"
    else:
        device_name = f"{row.get('network_name')} {row.get('device_model')}"
    
    # # Default parameters for add_monitor
    # monitor_params = {
    #     'type': MonitorType.JSON_QUERY,  # Using the enum from the library
    #     'name': device_name,
    #     'hostname': row.get('device_mac'),
    #     'description': row.get('device_serial'),
    #     'interval': 60, 
    #     'retryInterval': 60, 
    #     'maxretries': 1,
    #     'headers': row.get('headers'),
    #     'url': row.get('check_url'),
    #     'method': 'GET',
    #     'jsonPath': 'status',
    #     'jsonPathOperator': '==',
    #     'expectedValue': 'online'
    #     # Add other required parameters for PUSH type monitor if needed
    # }
    appsettings = m.appliance.getNetworkApplianceSettings(networkId=row.get('device_network_id'))
    url = appsettings.get('dynamicDns').get('url')

    # Extract the base URL without the domain part
    # if url:
    #     base_url_parts = url.split('.')
    #     base_url = base_url_parts[0]  # e.g., "kruse-and-associates-main-bvcrmqqvkwjc"
    #     domain_part = '.'.join(base_url_parts[1:])  # e.g., "dynamic-m.com"
        
    #     # Check if the device has a second WAN IP
    #     if not pd.isna(row['device_wan2_ip'].iloc[0]) and row['device_wan2_ip'].iloc[0]:
    #         # Calculate the two URLs with -1 and -2 suffixes
    #         url1 = f"{base_url}-1.{domain_part}"
    #         url2 = f"{base_url}-2.{domain_part}"
    #         two_monitors = True
    

    
    
    
    
    # Call add_monitor with the parameters
    try:

        monitor_params = {
            'type': MonitorType.PING,  # Using the enum from the library
            'name': f"{device_name}",
            'hostname': url,
            'description': row.get('device_serial'),
            'interval': 60, 
            'retryInterval': 60, 
            'maxretries': 1,
        }
        # If org_name exists and is in our lookup dictionary, add parent parameter
        if org_name and org_name in org_to_monitor_id:
            monitor_params['parent'] = org_to_monitor_id[org_name]
        result = api.add_monitor(**monitor_params)
        device_product_type = row.get('device_product_type')  
        for tag in tags:
            # Check if the device product type matches the tag name
            if device_product_type and device_product_type in tag.get('device_product_type'):
                try:
                    addtag_result = api.add_monitor_tag(
                        tag_id=tag['id'],
                        monitor_id=result.get('monitorID')
                    )
                    print(f"Added tag {tag['name']} to monitor {result.get('monitorID')}")
                except Exception as e:
                    print(f"Error adding tag {tag['name']} to monitor {result.get('monitorID')}: {e}")

    except Exception as e:
        print(e)