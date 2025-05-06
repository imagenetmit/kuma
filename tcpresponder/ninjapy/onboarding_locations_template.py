"""
Template configuration for Onboarding-Locations document template (ID: 23).
This template handles the mapping of location EDF data to NinjaRMM document fields.
"""

from typing import Dict, Any, List


def create_location_entity(org_id: int) -> Dict[str, Any]:
    """Create a location entity structure."""
    return {
        "entityId": org_id,
        "type": "CLIENT_LOCATION"
    }


def map_remote_support(data: List[Dict[str, Any]]) -> bool:
    """Check if either Remote Servers or Remote Workstations is True."""
    for item in data:
        if item['Title'] in ['Remote Servers', 'Remote Workstations']:
            if item.get('CheckboxValue', False):
                return True
    return False


def map_dns_filter(data: List[Dict[str, Any]]) -> bool:
    """Map DNS Filter enabled/disabled state."""
    for item in data:
        if item['Title'] == 'DNS Filter':
            return item.get('DropdownValue') == 'Enabled'
    return False


def map_dns_key(data: List[Dict[str, Any]]) -> str:
    """Extract DNS Filter software key."""
    for item in data:
        if item['Title'] == 'DNS Filter Software Key':
            return item.get('TextFieldValue') or None
    return None


def map_defensx(data: List[Dict[str, Any]]) -> bool:
    """Map DefensX enabled/disabled state."""
    for item in data:
        if item['Title'] == 'DefensX':
            return item.get('DropdownValue') == 'Enabled'
    return False


def map_defensx_key(data: List[Dict[str, Any]]) -> str:
    """Extract DefensX software key."""
    for item in data:
        if item['Title'] == 'DefensX Software Key':
            return item.get('TextFieldValue') or None
    return None


def map_location_name(data: List[Dict[str, Any]]) -> str:
    """Get location name from input data."""
    return data[0]['Name'] if data else None


# Template configuration
TEMPLATE_CONFIG = {
    "template_id": 23,
    "name": "Onboarding-Locations",
    "field_mappings": {
        "location": lambda data: create_location_entity(data[0]['organizationId']),
        "remoteSupportOnly": map_remote_support,
        "remoteservers": lambda data: any(
            item['Title'] == 'Remote Servers' and item.get('CheckboxValue', False) 
            for item in data
        ),
        "remoteworkstations": lambda data: any(
            item['Title'] == 'Remote Workstations' and item.get('CheckboxValue', False) 
            for item in data
        ),
        "deployDnsfilter": map_dns_filter,
        "dnsfilterlocationkey": map_dns_key,
        "deployDefensx": map_defensx,
        "defensxlocationkey": map_defensx_key,
        "documentName": map_location_name
    }
}


def register_template(client):
    """
    Register the Onboarding-Locations template with the NinjaRMM client.
    
    Args:
        client: NinjaRMM client instance
    """
    client.register_document_template(
        template_id=TEMPLATE_CONFIG["template_id"],
        name=TEMPLATE_CONFIG["name"],
        field_mappings=TEMPLATE_CONFIG["field_mappings"]
    ) 