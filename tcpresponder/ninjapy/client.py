import requests
from typing import Optional, Dict, List, Any, Union, Literal, Iterator
from datetime import datetime
from .exceptions import NinjaRMMError, NinjaRMMAuthError, NinjaRMMValidationError, NinjaRMMAPIError
from .auth import TokenManager
from .enums import NodeApprovalMode
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ninjapy.client')

class NinjaRMMClient:
    """
    Client for interacting with the NinjaRMM API v2.0.9-draft
    
    This client provides access to the NinjaOne Public API, including functionality for:
    - Organization management
    - Device management 
    - Policy management
    - Alert management
    - Custom fields
    - Location management
    """
    
    API_VERSION = "2.0.9-draft"
    DEFAULT_BASE_URL = "https://api.ninjarmm.com"
    
    # API Scopes
    SCOPE_MONITORING = "monitoring"
    SCOPE_MANAGEMENT = "management"
    SCOPE_CONTROL = "control"
    
    # Node Classes (from API spec)
    NODE_CLASS = Literal[
        "WINDOWS_SERVER", "WINDOWS_WORKSTATION", "LINUX_WORKSTATION", "MAC",
        "ANDROID", "APPLE_IOS", "APPLE_IPADOS", "VMWARE_VM_HOST", "VMWARE_VM_GUEST",
        "HYPERV_VMM_HOST", "HYPERV_VMM_GUEST", "LINUX_SERVER", "MAC_SERVER",
        "CLOUD_MONITOR_TARGET", "NMS_SWITCH", "NMS_ROUTER", "NMS_FIREWALL",
        "NMS_PRIVATE_NETWORK_GATEWAY", "NMS_PRINTER", "NMS_SCANNER", "NMS_DIAL_MANAGER",
        "NMS_WAP", "NMS_IPSLA", "NMS_COMPUTER", "NMS_VM_HOST", "NMS_APPLIANCE",
        "NMS_OTHER", "NMS_SERVER", "NMS_PHONE", "NMS_VIRTUAL_MACHINE",
        "NMS_NETWORK_MANAGEMENT_AGENT"
    ]
    
    def __init__(
        self, 
        token_url: str, 
        client_id: str, 
        client_secret: str, 
        scope: str,
        base_url: str = "https://app.ninjarmm.com"
    ) -> None:
        """
        Initialize the NinjaRMM API client.
        
        Args:
            token_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scope: OAuth2 scope(s)
            base_url: Base URL for the API. Defaults to https://api.ninjarmm.com
        """
        self.base_url = base_url.rstrip('/')
        self.token_manager = TokenManager(token_url, client_id, client_secret, scope)
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        # Configure retries with exponential backoff
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _request(
        self, 
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"], 
        endpoint: str, 
        **kwargs: Any
    ) -> Any:
        """
        Make a request to the API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            The JSON response from the API
            
        Raises:
            NinjaRMMAuthError: If authentication fails
            NinjaRMMError: If any other error occurs
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        # Get valid token before each request
        token = self.token_manager.get_valid_token()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Preparing request: {method} {url} with kwargs: {kwargs}")

        try:
            logger.info("Sending HTTP request now...")
            # Explicitly set a timeout to prevent indefinite hangs
            response = self.session.request(method, url, timeout=10, **kwargs)
            logger.info(f"HTTP request completed with status code: {response.status_code}")
            
            # Handle rate limiting explicitly
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 10))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                return self._request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            
            if response.status_code == 204:
                logger.info("Received 204 No Content response.")
                return None
                
            logger.info("Parsing JSON response.")
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out.")
            raise NinjaRMMError("Request timed out.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTPError encountered: {str(e)}")
            try:
                error_data = e.response.json()
                message = error_data.get('message', str(e))
            except ValueError:
                message = str(e)
                error_data = None
                
            if e.response.status_code == 401:
                raise NinjaRMMAuthError("Authentication failed")
            elif e.response.status_code == 403:
                raise NinjaRMMError("Permission denied")
            elif e.response.status_code == 404:
                raise NinjaRMMError("Resource not found")
            else:
                raise NinjaRMMAPIError(message, e.response.status_code, error_data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException encountered: {str(e)}")
            raise NinjaRMMError(f"Request failed: {str(e)}")

    def get_organizations(self, page_size: Optional[int] = None, after: Optional[int] = None, expand: Optional[str] = None,
                         org_filter: Optional[str] = None) -> List[Dict]:
        """
        Get list of organizations.
        
        Args:
            page_size: Limit number of organizations to return
            after: Last Organization Identifier from previous page
            org_filter: Organization filter
            
        Returns:
            List of organization objects
        """
        params = {}
        if page_size is not None:
            params['pageSize'] = page_size
        if after is not None:
            params['after'] = after
        if org_filter:
            params['of'] = org_filter
        if expand:
            params['expand'] = expand
        return self._request('GET', '/v2/organizations', params=params)
    
    def get_organizations_detailed(self, page_size: Optional[int] = None, after: Optional[int] = None, expand: Optional[str] = None,
                             org_filter: Optional[str] = None) -> List[Dict]:
        """
        Get list of organizations with detailed information.
        
        Args:
            page_size: Limit number of organizations to return
            after: Last Organization Identifier from previous page
            org_filter: Organization filter
            
        Returns:
            List of detailed organization objects including:
            - name: Organization full name
            - description: Organization description
            - userData: Custom attributes
            - nodeApprovalMode: Device approval mode (AUTOMATIC/MANUAL/REJECT)
            - tags: Organization tags
            - fields: Custom fields
            - id: Organization identifier
            - locations: List of locations
        """
        params = {}
        if page_size is not None:
            params['pageSize'] = page_size
        if after is not None:
            params['after'] = after
        if org_filter:
            params['of'] = org_filter
        if expand:
            params['expand'] = expand
        
        return self._request('GET', '/v2/organizations-detailed', params=params)

    def create_organization(self, name: str, description: Optional[str] = None,
                          template_org_id: Optional[int] = None, **kwargs) -> Dict:
        """
        Create a new organization.
        
        Args:
            name: Organization full name
            description: Organization description
            template_org_id: Model/Template organization to copy settings from
            **kwargs: Additional organization properties
            
        Returns:
            Dict: Created organization object
            
        Raises:
            NinjaRMMAuthError: If authentication fails
            NinjaRMMValidationError: If required fields are missing or invalid
            NinjaRMMAPIError: If organization creation fails
                - 403: Permission denied
                - 404: Template organization not found
                - 409: Organization with name already exists
        """
        data = {
            "name": name,
            **kwargs
        }
        if description:
            data["description"] = description
            
        params = {}
        if template_org_id:
            params["templateOrganizationId"] = template_org_id
            
        return self._request('POST', '/v2/organizations', json=data, params=params)

    def approve_devices(self, device_ids: List[int]) -> None:
        """
        Approve devices that are waiting for approval.
        
        Args:
            device_ids (List[int]): List of device IDs to approve
        """
        data = {"devices": device_ids}
        self._request('POST', '/v2/devices/approval/APPROVE', json=data)

    def reject_devices(self, device_ids: List[int]) -> None:
        """
        Reject devices that are waiting for approval.
        
        Args:
            device_ids (List[int]): List of device IDs to reject
        """
        data = {"devices": device_ids}
        self._request('POST', '/v2/devices/approval/REJECT', json=data)

    def reset_alert(self, alert_uid: str) -> None:
        """
        Reset an alert/condition by UID.
        
        Args:
            alert_uid (str): Alert/condition UID
        """
        self._request('DELETE', f'/v2/alert/{alert_uid}')

    def reset_alert_with_data(self, alert_uid: str, activity_data: Dict) -> None:
        """
        Reset an alert/condition and provide custom data for activity.
        
        Args:
            alert_uid (str): Alert/condition UID
            activity_data (Dict): Custom activity data
        """
        self._request('POST', f'/v2/alert/{alert_uid}/reset', json=activity_data)

    def get_organization(self, org_id: int) -> Dict:
        """
        Get a specific organization by ID.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            Organization object
        """
        return self._request('GET', f'/v2/organizations/{org_id}')

    def update_organization(
        self, 
        org_id: int, 
        name: str, 
        description: Optional[str] = None,
        node_approval_mode: Optional[NodeApprovalMode] = None,
        **kwargs
    ) -> Dict:
        """Update an existing organization."""
        if node_approval_mode and not isinstance(node_approval_mode, NodeApprovalMode):
            raise NinjaRMMValidationError(
                "Invalid node_approval_mode",
                "node_approval_mode"
            )
        data = {
            "name": name,
            **kwargs
        }
        if description:
            data["description"] = description
        if node_approval_mode:
            data["nodeApprovalMode"] = node_approval_mode

        return self._request('PATCH', f'/v2/organizations/{org_id}', json=data)

    def delete_organization(self, org_id: int) -> None:
        """
        Delete an organization.
        
        Args:
            org_id: Organization identifier
            
        Raises:
            NinjaRMMAuthError: If authentication fails
            NinjaRMMAPIError: If deletion fails
                - 403: Permission denied
                - 404: Organization not found
                - 409: Organization has active devices
        """
        self._request('DELETE', f'/v2/organizations/{org_id}')

    def get_organization_settings(self, org_id: int) -> Dict:
        """
        Get organization settings.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            Organization settings object
        """
        return self._request('GET', f'/v2/organizations/{org_id}/settings')

    def update_organization_settings(self, org_id: int, settings: Dict) -> Dict:
        """
        Update organization settings.
        
        Args:
            org_id (int): Organization identifier
            settings (Dict): Settings object containing configuration for features like
                           trayicon, splashtop, teamviewer, backup, psa
            
        Returns:
            Updated organization settings
        """
        return self._request('PUT', f'/v2/organizations/{org_id}/settings', json=settings)

    def get_organization_locations(self, org_id: int) -> List[Dict]:
        """
        Get organization locations.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            List of location objects
        """
        return self._request('GET', f'/v2/organizations/{org_id}/locations')

    def create_organization_location(self, org_id: int, name: str, address: Optional[str] = None,
                                  description: Optional[str] = None, **kwargs) -> Dict:
        """
        Create a new location for an organization.
        
        Args:
            org_id (int): Organization identifier
            name (str): Location name
            address (str, optional): Location address
            description (str, optional): Location description
            **kwargs: Additional location properties like tags, fields, userData
            
        Returns:
            Created location object
        """
        data = {
            "name": name,
            **kwargs
        }
        if address:
            data["address"] = address
        if description:
            data["description"] = description

        return self._request('POST', f'/v2/organizations/{org_id}/locations', json=data)

    def update_organization_location(self, org_id: int, location_id: int, name: str,
                                  address: Optional[str] = None, description: Optional[str] = None,
                                  **kwargs) -> Dict:
        """
        Update an organization location.
        
        Args:
            org_id (int): Organization identifier
            location_id (int): Location identifier
            name (str): Location name
            address (str, optional): Location address
            description (str, optional): Location description
            **kwargs: Additional location properties like tags, fields, userData
            
        Returns:
            Updated location object
        """
        data = {
            "name": name,
            **kwargs
        }
        if address:
            data["address"] = address
        if description:
            data["description"] = description

        return self._request('PATCH', f'/v2/organizations/{org_id}/locations/{location_id}', json=data)

    def delete_organization_location(self, org_id: int, location_id: int) -> None:
        """
        Delete an organization location.
        
        Args:
            org_id (int): Organization identifier
            location_id (int): Location identifier
        """
        self._request('DELETE', f'/v2/organizations/{org_id}/locations/{location_id}')

    def get_organization_policies(self, org_id: int) -> List[Dict]:
        """
        Get organization policy mappings.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            List of policy mapping objects
        """
        return self._request('GET', f'/v2/organizations/{org_id}/policies')

    def update_organization_policies(self, org_id: int, policies: List[Dict]) -> List[Dict]:
        """
        Update organization policy mappings.
        
        Args:
            org_id (int): Organization identifier
            policies (List[Dict]): List of policy mappings containing nodeRoleId and policyId
            
        Returns:
            Updated list of policy mapping objects
        """
        return self._request('PUT', f'/v2/organizations/{org_id}/policies', json=policies)

    def get_devices(self, page_size: Optional[int] = None, after: Optional[int] = None,
                   org_filter: Optional[str] = None, expand: Optional[str] = None, include_backup_usage: bool = False) -> List[Dict]:
        """
        Get list of devices.
        
        Args:
            page_size (int, optional): Limit number of devices to return
            after (int, optional): Last Device Identifier from previous page
            org_filter (str, optional): Organization filter
            expand (str, optional): Expand options
            include_backup_usage (bool): Include backup usage information
            
        Returns:
            List of device objects
        """
        params = {}
        if page_size:
            params['pageSize'] = page_size
        if after:
            params['after'] = after
        if org_filter:
            params['of'] = org_filter
        if expand:
            params['expand'] = expand
        if include_backup_usage:
            params['includeBackupUsage'] = 'true'
            
        return self._request('GET', '/v2/devices', params=params)

    def get_devices_detailed(self, page_size: Optional[int] = None, after: Optional[int] = None,
                   org_filter: Optional[str] = None, expand: Optional[str] = None, include_backup_usage: bool = False) -> List[Dict]:
        """
        Get detailed list of devices.
        
        Args:
            page_size (int, optional): Limit number of devices to return
            after (int, optional): Last Device Identifier from previous page
            org_filter (str, optional): Organization filter
            expand (str, optional): Expand options
            include_backup_usage (bool): Include backup usage information

        Returns:
            List of device objects
        """
        params = {}
        if page_size:
            params['pageSize'] = page_size
        if after:
            params['after'] = after
        if org_filter:
            params['of'] = org_filter
        if expand:
            params['expand'] = expand
        if include_backup_usage:
            params['includeBackupUsage'] = 'true'
            
        return self._request('GET', '/v2/devices-detailed', params=params)

    def get_device(self, device_id: int, expand: Optional[str] = None, include_backup_usage: bool = False) -> Dict:
        """
        Get a specific device by ID.
        
        Args:
            device_id (int): Device identifier
            include_backup_usage (bool): Include backup usage information
            expand (str, optional): Expand options
        Returns:
            Device object
        """
        params = {}
        if include_backup_usage:
            params['includeBackupUsage'] = 'true'
        if expand:
            params['expand'] = expand
            
        return self._request('GET', f'/v2/devices/{device_id}', params=params)

    def update_device(self, device_id: int, **kwargs) -> Dict:
        """
        Update a device.
        
        Args:
            device_id (int): Device identifier
            **kwargs: Device properties to update (displayName, systemName, nodeRoleId, policyId, etc.)
            
        Returns:
            Updated device object
        """
        return self._request('PATCH', f'/v2/devices/{device_id}', json=kwargs)

    def delete_device(self, device_id: int) -> None:
        """
        Delete a device.
        
        Args:
            device_id (int): Device identifier
        """
        self._request('DELETE', f'/v2/devices/{device_id}')

    def search_devices(self, query: str, page_size: Optional[int] = None,
                      cursor: Optional[str] = None, **kwargs) -> Dict:
        """
        Search for devices using query string.
        
        Args:
            query (str): Search query string
            page_size (int, optional): Number of results per page
            cursor (str, optional): Cursor for pagination
            **kwargs: Additional parameters to pass to the API  
            
        Returns:
            Search results containing devices and metadata
        """
        params = {'q': query}
        if page_size:
            params['pageSize'] = page_size
        if cursor:
            params['cursor'] = cursor
        params.update(kwargs)
            
        return self._request('GET', '/v2/devices/search', params=params)

    def get_device_alerts(self, device_id: int) -> List[Dict]:
        """
        Get alerts for a specific device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of alert objects
        """
        return self._request('GET', f'/v2/devices/{device_id}/alerts')

    def get_device_activities(self, device_id: int, start_time: Optional[float] = None,
                            end_time: Optional[float] = None, activity_type: Optional[str] = None,
                            page_size: Optional[int] = None, cursor: Optional[str] = None) -> Dict:
        """
        Get activities for a specific device.
        
        Args:
            device_id (int): Device identifier
            start_time (float, optional): Start time in epoch seconds
            end_time (float, optional): End time in epoch seconds
            activity_type (str, optional): Filter by activity type
            page_size (int, optional): Number of results per page
            cursor (str, optional): Cursor for pagination
            
        Returns:
            Activities and pagination metadata
        """
        params = {}
        if start_time:
            params['from'] = start_time
        if end_time:
            params['to'] = end_time
        if activity_type:
            params['type'] = activity_type
        if page_size:
            params['pageSize'] = page_size
        if cursor:
            params['cursor'] = cursor
            
        return self._request('GET', f'/v2/devices/{device_id}/activities', params=params)

    def get_device_processes(self, device_id: int) -> List[Dict]:
        """
        Get running processes for a specific device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of process objects
        """
        return self._request('GET', f'/v2/devices/{device_id}/processes')

    def get_device_services(self, device_id: int) -> List[Dict]:
        """
        Get services for a specific device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of service objects
        """
        return self._request('GET', f'/v2/devices/{device_id}/services')

    def get_device_software(self, device_id: int) -> List[Dict]:
        """
        Get installed software for a specific device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of software objects
        """
        return self._request('GET', f'/v2/devices/{device_id}/software')

    def get_device_volumes(self, device_id: int) -> List[Dict]:
        """
        Get disk volumes for a specific device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of volume objects
        """
        return self._request('GET', f'/v2/devices/{device_id}/volumes')

    def enable_maintenance_mode(self, device_id: int, duration: int) -> Dict:
        """
        Enable maintenance mode for a device.
        
        Args:
            device_id (int): Device identifier
            duration (int): Duration in seconds
            
        Returns:
            Updated device maintenance status
        """
        return self._request('POST', f'/v2/devices/{device_id}/maintenance', 
                           json={'duration': duration})

    def disable_maintenance_mode(self, device_id: int) -> None:
        """
        Disable maintenance mode for a device.
        
        Args:
            device_id (int): Device identifier
        """
        self._request('DELETE', f'/v2/devices/{device_id}/maintenance')

    def get_custom_fields_policy_conditions(self, policy_id: int) -> List[Dict]:
        """
        Get all custom fields policy conditions for specified policy.
        
        Args:
            policy_id (int): Policy identifier
            
        Returns:
            List of custom fields policy conditions
        """
        return self._request('GET', f'/v2/policies/{policy_id}/condition/custom-fields')

    def create_custom_fields_policy_condition(self, policy_id: int, display_name: str,
                                           match_all: Optional[List[Dict]] = None,
                                           match_any: Optional[List[Dict]] = None,
                                           **kwargs) -> Dict:
        """
        Creates custom fields policy condition for specified policy.
        
        Args:
            policy_id (int): Policy identifier
            display_name (str): Policy condition display name
            match_all (List[Dict], optional): Custom field conditions that must all match
            match_any (List[Dict], optional): Custom field conditions where any can match
            **kwargs: Additional condition properties (enabled, severity, priority, etc.)
            
        Returns:
            Created policy condition
        """
        data = {
            "displayName": display_name,
            **kwargs
        }
        if match_all:
            data["matchAll"] = match_all
        if match_any:
            data["matchAny"] = match_any
            
        return self._request('POST', f'/v2/policies/{policy_id}/condition/custom-fields', json=data)

    def get_custom_fields_policy_condition(self, policy_id: int, condition_id: str) -> Dict:
        """
        Get specified custom fields condition for specified policy.
        
        Args:
            policy_id (int): Policy identifier
            condition_id (str): Condition identifier
            
        Returns:
            Policy condition details
        """
        return self._request('GET', f'/v2/policies/{policy_id}/condition/custom-fields/{condition_id}')

    def get_windows_event_conditions(self, policy_id: int) -> List[Dict]:
        """
        Get all windows event conditions for specified policy.
        
        Args:
            policy_id (int): Policy identifier
            
        Returns:
            List of windows event conditions
        """
        return self._request('GET', f'/v2/policies/{policy_id}/condition/windows-event')

    def create_windows_event_condition(self, policy_id: int, source: str, event_ids: List[int],
                                    display_name: str, **kwargs) -> Dict:
        """
        Creates windows event condition for specified policy.
        
        Args:
            policy_id (int): Policy identifier
            source (str): Event Source
            event_ids (List[int]): List of Event IDs to monitor
            display_name (str): Policy condition display name
            **kwargs: Additional condition properties (enabled, severity, priority, etc.)
            
        Returns:
            Created windows event condition
        """
        data = {
            "source": source,
            "eventIds": event_ids,
            "displayName": display_name,
            **kwargs
        }
        return self._request('POST', f'/v2/policies/{policy_id}/condition/windows-event', json=data)

    def get_windows_event_condition(self, policy_id: int, condition_id: str) -> Dict:
        """
        Get specified windows event condition for specified policy.
        
        Args:
            policy_id (int): Policy identifier
            condition_id (str): Condition identifier
            
        Returns:
            Windows event condition details
        """
        return self._request('GET', f'/v2/policies/{policy_id}/condition/windows-event/{condition_id}')

    def delete_policy_condition(self, policy_id: int, condition_id: str) -> None:
        """
        Deletes specified policy condition from specified agent policy.
        
        Args:
            policy_id (int): Policy identifier
            condition_id (str): Condition identifier
        """
        self._request('DELETE', f'/v2/policies/{policy_id}/condition/{condition_id}')

    def configure_webhook(self, url: str, activities: Dict[str, List[str]], 
                        expand: Optional[List[str]] = None,
                        headers: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Creates or updates Webhook configuration for current application/client.
        
        Args:
            url (str): Callback (WebHook) URL for activity notifications
            activities (Dict[str, List[str]]): Activity filter mapping
            expand (List[str], optional): References to expand in payloads
            headers (List[Dict[str, str]], optional): Custom HTTP Headers
        """
        data = {
            "url": url,
            "activities": activities
        }
        if expand:
            data["expand"] = expand
        if headers:
            data["headers"] = headers
            
        self._request('PUT', '/v2/webhook', json=data)

    def disable_webhook(self) -> None:
        """
        Disables Webhook configuration for current application/client.
        """
        self._request('DELETE', '/v2/webhook')

    def list_policies(self) -> List[Dict]:
        """
        List all policies.
        
        Returns:
            List of policy objects
        """
        return self._request('GET', '/v2/policies')

    def list_active_jobs(self) -> List[Dict]:
        """
        List all active jobs.
        
        Returns:
            List of active job objects
        """
        return self._request('GET', '/v2/jobs')

    def list_activities(self, start_time: Optional[float] = None, end_time: Optional[float] = None,
                       activity_type: Optional[str] = None, page_size: Optional[int] = None,
                       cursor: Optional[str] = None) -> Dict:
        """
        List all activities.
        
        Args:
            start_time (float, optional): Start time in epoch seconds
            end_time (float, optional): End time in epoch seconds
            activity_type (str, optional): Filter by activity type
            page_size (int, optional): Number of results per page
            cursor (str, optional): Cursor for pagination
            
        Returns:
            Activities and pagination metadata
        """
        params = {}
        if start_time:
            params['from'] = start_time
        if end_time:
            params['to'] = end_time
        if activity_type:
            params['type'] = activity_type
        if page_size:
            params['pageSize'] = page_size
        if cursor:
            params['cursor'] = cursor
            
        return self._request('GET', '/v2/activities', params=params)

    def list_active_alerts(self) -> List[Dict]:
        """
        List all active alerts (triggered conditions).
        
        Returns:
            List of active alert objects
        """
        return self._request('GET', '/v2/alerts')

    def list_automation_scripts(self) -> List[Dict]:
        """
        List all available automation scripts.
        
        Returns:
            List of automation script objects
        """
        return self._request('GET', '/v2/automation/scripts')

    def list_device_custom_fields(self) -> List[Dict]:
        """
        Get all device custom fields.
        
        Returns:
            List of custom field objects
        """
        return self._request('GET', '/v2/device-custom-fields')

    def list_devices_detailed(self, page_size: Optional[int] = None, 
                            after: Optional[int] = None) -> List[Dict]:
        """
        List devices with detailed information.
        
        Args:
            page_size (int, optional): Limit number of devices to return
            after (int, optional): Last Device Identifier from previous page
            
        Returns:
            List of detailed device objects
        """
        params = {}
        if page_size:
            params['pageSize'] = page_size
        if after:
            params['after'] = after
            
        return self._request('GET', '/v2/devices-detailed', params=params)

    def list_enabled_notification_channels(self) -> List[Dict]:
        """
        List all enabled notification channels.
        
        Returns:
            List of enabled notification channel objects
        """
        return self._request('GET', '/v2/notification-channels/enabled')

    def list_groups(self) -> List[Dict]:
        """
        List all groups (saved searches).
        
        Returns:
            List of group objects
        """
        return self._request('GET', '/v2/groups')

    def list_locations(self) -> List[Dict]:
        """
        List all locations.
        
        Returns:
            List of location objects
        """
        return self._request('GET', '/v2/locations')

    def list_device_roles(self) -> List[Dict]:
        """
        List all device roles.
        
        Returns:
            List of device role objects
        """
        return self._request('GET', '/v2/roles')

    def list_notification_channels(self) -> List[Dict]:
        """
        List all notification channels.
        
        Returns:
            List of notification channel objects
        """
        return self._request('GET', '/v2/notification-channels')

    def list_organizations_detailed(self, page_size: Optional[int] = None,
                                 after: Optional[int] = None) -> List[Dict]:
        """
        List organizations with detailed information.
        
        Args:
            page_size (int, optional): Limit number of organizations to return
            after (int, optional): Last Organization Identifier from previous page
            
        Returns:
            List of detailed organization objects
        """
        params = {}
        if page_size:
            params['pageSize'] = page_size
        if after:
            params['after'] = after
            
        return self._request('GET', '/v2/organizations-detailed', params=params)

    def list_scheduled_tasks(self) -> List[Dict]:
        """
        List all scheduled tasks.
        
        Returns:
            List of scheduled task objects
        """
        return self._request('GET', '/v2/tasks')

    def list_software_products(self) -> List[Dict]:
        """
        List all supported 3rd party software.
        
        Returns:
            List of software product objects
        """
        return self._request('GET', '/v2/software-products')

    def list_users(self) -> List[Dict]:
        """
        List all users.
        
        Returns:
            List of user objects
        """
        return self._request('GET', '/v2/users')

    def get_organization_end_users(self, org_id: int) -> List[Dict]:
        """
        Get list of end users for an organization.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            List of end user objects
        """
        return self._request('GET', f'/v2/organization/{org_id}/end-users')

    def get_organization_location_backup_usage(self, org_id: int, location_id: int) -> Dict:
        """
        Get backup usage for a specific organization location.
        
        Args:
            org_id (int): Organization identifier
            location_id (int): Location identifier
            
        Returns:
            Backup usage information
        """
        return self._request('GET', f'/v2/organization/{org_id}/locations/{location_id}/backup/usage')

    def get_organization_custom_fields(self, org_id: int) -> List[Dict]:
        """
        Get custom fields for an organization.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            List of custom field objects
        """
        return self._request('GET', f'/v2/organization/{org_id}/custom-fields')

    def update_organization_custom_fields(self, org_id: int, custom_fields: Dict) -> Dict:
        """
        Update custom field values for an organization.
        
        Args:
            org_id (int): Organization identifier
            custom_fields (Dict): Custom field values to update
            
        Returns:
            Updated custom fields
        """
        return self._request('PATCH', f'/v2/organization/{org_id}/custom-fields', json=custom_fields)

    def get_organization_devices(self, org_id: int) -> List[Dict]:
        """
        Get all devices for an organization.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            List of device objects
        """
        return self._request('GET', f'/v2/organization/{org_id}/devices')

    def get_organization_locations_backup_usage(self, org_id: int) -> Dict:
        """
        Get backup usage for all locations in an organization.
        
        Args:
            org_id (int): Organization identifier
            
        Returns:
            Backup usage information for all locations
        """
        return self._request('GET', f'/v2/organization/{org_id}/locations/backup/usage')

    def get_device_jobs(self, device_id: int) -> List[Dict]:
        """
        Get currently running (active) jobs for a device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of active job objects
        """
        return self._request('GET', f'/v2/device/{device_id}/jobs')

    def get_device_disks(self, device_id: int) -> List[Dict]:
        """
        Get disk drives for a device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of disk drive objects
        """
        return self._request('GET', f'/v2/device/{device_id}/disks')

    def get_device_os_patch_installs(self, device_id: int) -> List[Dict]:
        """
        Get OS Patch installation report for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of OS patch installation reports
        """
        return self._request('GET', f'/v2/device/{device_id}/os-patch-installs')

    def get_device_software_patch_installs(self, device_id: int) -> List[Dict]:
        """
        Get Software Patch history for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of software patch installation history
        """
        return self._request('GET', f'/v2/device/{device_id}/software-patch-installs')

    def get_device_last_logged_on_user(self, device_id: int) -> Dict:
        """
        Get last logged-on user information for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            Last logged-on user information
        """
        return self._request('GET', f'/v2/device/{device_id}/last-logged-on-user')

    def get_device_network_interfaces(self, device_id: int) -> List[Dict]:
        """
        Get network interfaces for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of network interface objects
        """
        return self._request('GET', f'/v2/device/{device_id}/network-interfaces')

    def get_device_os_patches(self, device_id: int) -> List[Dict]:
        """
        Get OS Patches for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of OS patch objects
        """
        return self._request('GET', f'/v2/device/{device_id}/os-patches')

    def get_device_software_patches(self, device_id: int) -> List[Dict]:
        """
        Get Pending, Failed and Rejected Software patches for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of software patch objects
        """
        return self._request('GET', f'/v2/device/{device_id}/software-patches')

    def get_device_processors(self, device_id: int) -> List[Dict]:
        """
        Get processors for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of processor objects
        """
        return self._request('GET', f'/v2/device/{device_id}/processors')

    def get_device_windows_services(self, device_id: int) -> List[Dict]:
        """
        Get Windows services for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            List of Windows service objects
        """
        return self._request('GET', f'/v2/device/{device_id}/windows-services')

    def get_device_custom_fields(self, device_id: int) -> Dict:
        """
        Get custom fields for device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            Device custom fields
        """
        return self._request('GET', f'/v2/device/{device_id}/custom-fields')

    def update_device_custom_fields(self, device_id: int, custom_fields: Dict) -> Dict:
        """
        Update custom field values for device.
        
        Args:
            device_id (int): Device identifier
            custom_fields (Dict): Custom field values to update
            
        Returns:
            Updated device custom fields
        """
        return self._request('PATCH', f'/v2/device/{device_id}/custom-fields', json=custom_fields)

    def get_device_policy_overrides(self, device_id: int) -> Dict:
        """
        Get summary of device policy overrides.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            Device policy override summary
        """
        return self._request('GET', f'/v2/device/{device_id}/policy/overrides')

    def control_windows_service(
        self, 
        device_id: int, 
        service_id: str, 
        action: Literal["START", "STOP", "RESTART", "PAUSE", "RESUME"]
    ) -> None:
        """Control a Windows service on a device."""
        if action not in ("START", "STOP", "RESTART", "PAUSE", "RESUME"):
            raise NinjaRMMValidationError(
                "Invalid service control action",
                "action"
            )

    def get_device_dashboard_url(self, device_id: int) -> str:
        """
        Get dashboard URL for a device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            Dashboard URL string
        """
        return self._request('GET', f'/v2/device/{device_id}/dashboard-url')

    def reset_device_policy_overrides(self, device_id: int) -> None:
        """
        Reset all policy overrides for a device.
        
        Args:
            device_id (int): Device identifier
        """
        self._request('DELETE', f'/v2/device/{device_id}/policy/overrides')

    def reboot_device(self, device_id: int, mode: Literal["FORCE", "GRACEFUL"]) -> None:
        """
        Reboot a device.
        
        Args:
            device_id: Device identifier
            mode: Reboot mode, must be one of:
                - "FORCE": Force immediate reboot
                - "GRACEFUL": Allow graceful shutdown
                
        Raises:
            NinjaRMMValidationError: If mode is not "FORCE" or "GRACEFUL"
        """
        if mode not in ("FORCE", "GRACEFUL"):
            raise NinjaRMMValidationError(
                "Invalid reboot mode. Must be 'FORCE' or 'GRACEFUL'",
                "mode"
            )
        self._request('POST', f'/v2/device/{device_id}/reboot/{mode}')

    def remove_device_owner(self, device_id: int) -> None:
        """
        Remove owner from a device.
        
        Args:
            device_id (int): Device identifier
        """
        self._request('DELETE', f'/v2/device/{device_id}/owner')

    def get_device_scripting_options(self, device_id: int) -> Dict:
        """
        Get scripting options for a device.
        
        Args:
            device_id (int): Device identifier
            
        Returns:
            Device scripting options
        """
        return self._request('GET', f'/v2/device/{device_id}/scripting/options')

    def run_device_script(self, device_id: int, script_id: int, **kwargs) -> Dict:
        """
        Run a script or built-in action on a device.
        
        Args:
            device_id (int): Device identifier
            script_id (int): Script identifier
            **kwargs: Additional script parameters
            
        Returns:
            Script execution result
        """
        data = {
            "scriptId": script_id,
            **kwargs
        }
        return self._request('POST', f'/v2/device/{device_id}/script/run', json=data)

    def set_device_owner(self, device_id: int, owner_uid: str) -> None:
        """
        Set owner for a device.
        
        Args:
            device_id (int): Device identifier
            owner_uid (str): Owner user ID
        """
        self._request('POST', f'/v2/device/{device_id}/owner/{owner_uid}')

    def configure_windows_service(self, device_id: int, service_id: str, config: Dict) -> None:
        """
        Modify Windows Service configuration.
        
        Args:
            device_id (int): Device identifier
            service_id (str): Service identifier
            config (Dict): Service configuration
        """
        self._request('POST', f'/v2/device/{device_id}/windows-service/{service_id}/configure', 
                     json=config)

    def generate_organization_installer(self, **kwargs) -> Dict:
        """
        Generate installer for organization.
        
        Args:
            **kwargs: Installer generation parameters
            
        Returns:
            Installer information
        """
        return self._request('POST', '/v2/organization/generate-installer', json=kwargs)

    def generate_location_installer(self, org_id: int, location_id: int, 
                                 installer_type: str) -> Dict:
        """
        Generate installer for specific location.
        
        Args:
            org_id (int): Organization identifier
            location_id (int): Location identifier
            installer_type (str): Type of installer
            
        Returns:
            Installer information
        """
        return self._request('GET', 
                           f'/v2/organization/{org_id}/location/{location_id}/installer/{installer_type}')

    def create_policy(self, name: str, **kwargs) -> Dict:
        """
        Create a new policy.
        
        Args:
            name (str): Policy name
            **kwargs: Additional policy properties
            
        Returns:
            Created policy object
        """
        data = {
            "name": name,
            **kwargs
        }
        return self._request('POST', '/v2/policies', json=data)

    def get_location_custom_fields(self, org_id: int, location_id: int) -> Dict:
        """
        Get custom fields for a specific location.
        
        Args:
            org_id (int): Organization identifier
            location_id (int): Location identifier
            
        Returns:
            Location custom fields
        """
        return self._request('GET', 
                           f'/v2/organization/{org_id}/location/{location_id}/custom-fields')

    def update_location_custom_fields(self, org_id: int, location_id: int, 
                                    custom_fields: Dict) -> Dict:
        """
        Update custom field values for a specific location.
        
        Args:
            org_id (int): Organization identifier
            location_id (int): Location identifier
            custom_fields (Dict): Custom field values to update
            
        Returns:
            Updated location custom fields
        """
        return self._request('PATCH',
                           f'/v2/organization/{org_id}/location/{location_id}/custom-fields',
                           json=custom_fields)

    def create_document_from_template(
        self,
        input_data: Dict[str, Any],
        template_id: int,
        org_id: int
    ) -> Dict:
        """
        Create a document using a registered template.
        
        Args:
            input_data (Dict[str, Any]): Input JSON data containing the values to store
            template_id (int): The template ID to use
            org_id (int): Organization ID
            
        Returns:
            Dict: Created document
            
        Raises:
            ValueError: If template_id is not registered
        """
        from .document_templates import template_registry
        
        # Get template configuration
        template = template_registry.get_template_by_id(template_id)
        if template is None:
            raise ValueError(f"No template registered for template_id: {template_id}")
            
        # Transform data using template
        document_body = template.transform_data(input_data, org_id)
        
        # Create document
        return self.create_organization_document(
            organization_id=org_id,
            document_template_id=template_id,
            document_name=document_body["documentName"],
            document_description=document_body.get("documentDescription"),
            fields=document_body["fields"]
        )

    def __enter__(self) -> 'NinjaRMMClient':
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        
    def close(self) -> None:
        """Close the session and cleanup resources."""
        self.session.close()

    def iter_organizations(self, page_size: int = 100) -> Iterator[Dict]:
        """
        Iterate through all organizations using pagination.
        
        Args:
            page_size: Number of items per page
            
        Yields:
            Organization objects one at a time
        """
        last_id = None
        while True:
            page = self.get_organizations(page_size=page_size, after=last_id)
            if not page:
                break
            yield from page
            last_id = page[-1]["id"] 

    def create_location(self, org_id: int, name: str, description: str = None, address: str = None) -> dict:
        """Create a new location for an organization

        Args:
            org_id (int): Organization ID
            name (str): Location name
            description (str, optional): Location description. Defaults to None.
            address (str, optional): Location address. Defaults to None.

        Returns:
            dict: Created location object
        """
        url = f"{self.base_url}/v2/organization/{org_id}/locations"
        data = {
            "name": name,
            "description": description,
            "address": address
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json() 

    def get_location(self, org_id: int) -> List[Dict]:
        """Get all locations for an organization

        Args:
            org_id (int): Organization ID

        Returns:
            List[Dict]: List of location objects
        """
        url = f"{self.base_url}/v2/organization/{org_id}/locations"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json() 
    
    def get_locations(self) -> List[Dict]:
        """Get all locations for an organization


        Returns:
            List[Dict]: List of location objects
        """
        url = f"{self.base_url}/v2/locations"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json() 

    def update_location(self, org_id: int, location_id: int, name: str = None, description: str = None, address: str = None) -> Dict:
        """Update an existing location for an organization

        Args:
            org_id (int): Organization ID
            location_id (int): Location ID to update
            name (str, optional): Location name. Defaults to None.
            description (str, optional): Location description. Defaults to None.
            address (str, optional): Location address. Defaults to None.

        Returns:
            Dict: Updated location object
        """
        url = f"{self.base_url}/v2/organization/{org_id}/locations/{location_id}"
        data = {
            "name": name,
            "description": description,
            "address": address
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        response = self.session.patch(url, json=data)
        response.raise_for_status()
        return response.json() 

    def create_organization_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Create multiple organization documents.
        
        Args:
            documents (List[Dict]): List of documents to create, each containing:
                - documentName (str): Document name
                - documentDescription (str, optional): Document description
                - fields (Dict, optional): Document fields as key-value pairs
                - documentTemplateId (int): Document template identifier
                - organizationId (int): Organization identifier
                
        Returns:
            List[Dict]: List of created organization documents containing:
                - documentId (int): Document identifier
                - documentName (str): Document name
                - documentDescription (str): Document description
                - documentUpdateTime (float): Document last updated
                - fields (List[Dict]): Updated fields
                - documentTemplateId (int): Document template identifier
                - documentTemplateName (str): Document template name
                - organizationId (int): Organization identifier
        """
        # Ensure documents is a list
        if isinstance(documents, dict):
            documents = [documents]
        elif not isinstance(documents, list):
            raise ValueError("documents must be a list of dictionaries or a single dictionary")

        # Process each document to remove None values from fields
        processed_documents = []
        for doc in documents:
            if not isinstance(doc, dict):
                raise ValueError("Each document must be a dictionary")
                
            processed_doc = doc.copy()
            if 'fields' in processed_doc and isinstance(processed_doc['fields'], dict):
                # Remove None values from fields
                processed_doc['fields'] = {k: v for k, v in processed_doc['fields'].items() if v is not None}
            processed_documents.append(processed_doc)
            
        return self._request('POST', '/v2/organization/documents', json=processed_documents)

    def create_organization_document(
        self,
        organization_id: int,
        document_template_id: int,
        document_name: str,
        document_description: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Create a single organization document.

        Args:
            organization_id (int): Organization identifier
            document_template_id (int): Document template identifier
            document_name (str): Document name
            document_description (str, optional): Document description
            fields (Dict[str, Any], optional): Document fields as key-value pairs

        Returns:
            Dict: Created organization document
        """
        document = {
            "documentName": document_name,
            "documentTemplateId": document_template_id,
            "organizationId": organization_id
        }
        
        if document_description is not None:
            document["documentDescription"] = document_description
        if fields is not None:
            if not isinstance(fields, dict):
                raise ValueError("fields must be a dictionary")
            # Remove None values from fields
            document["fields"] = {k: v for k, v in fields.items() if v is not None}

        # Create a single document using the bulk endpoint
        return self.create_organization_documents(document)[0]

    def update_organization_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Update multiple organization documents.
        
        Args:
            documents (List[Dict]): List of documents to update, each containing:
                - documentId (int): Document identifier
                - documentName (str, optional): Document name
                - documentDescription (str, optional): Document description
                - fields (Dict, optional): Document fields as key-value pairs
                
        Returns:
            List[Dict]: List of updated organization documents
        """
        # Ensure documents is a list
        if isinstance(documents, dict):
            documents = [documents]
        elif not isinstance(documents, list):
            raise ValueError("documents must be a list of dictionaries or a single dictionary")

        # Process each document to remove None values from fields
        processed_documents = []
        for doc in documents:
            if not isinstance(doc, dict):
                raise ValueError("Each document must be a dictionary")
                
            processed_doc = doc.copy()
            if 'fields' in processed_doc and isinstance(processed_doc['fields'], dict):
                # Remove None values from fields
                processed_doc['fields'] = {k: v for k, v in processed_doc['fields'].items() if v is not None}
            processed_documents.append(processed_doc)
            
        return self._request('PATCH', '/v2/organization/documents', json=processed_documents)

    def update_organization_document(
        self,
        document_id: int,
        document_name: Optional[str] = None,
        document_description: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Update a single organization document.

        Args:
            document_id (int): Document identifier
            document_name (str, optional): Document name
            document_description (str, optional): Document description
            fields (Dict[str, Any], optional): Document fields as key-value pairs

        Returns:
            Dict: Updated organization document
        """
        document = {}
        
        if document_name is not None:
            document["documentName"] = document_name
        if document_description is not None:
            document["documentDescription"] = document_description
        if fields is not None:
            if not isinstance(fields, dict):
                raise ValueError("fields must be a dictionary")
            # Remove None values from fields
            document["fields"] = {k: v for k, v in fields.items() if v is not None}

        return self._request('PATCH', f'/v2/organization/documents/{document_id}', json=document)

    def update_document_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mandatory: Optional[bool] = None,
        fields: Optional[List[Dict]] = None,
        available_to_all_technicians: Optional[bool] = None,
        allowed_technician_roles: Optional[List[int]] = None
    ) -> Dict:
        """
        Update a document template.

        Args:
            template_id (int): Template identifier
            name (str, optional): Template name
            description (str, optional): Template description
            mandatory (bool, optional): Whether document is mandatory
            fields (List[Dict], optional): Template fields configuration
            available_to_all_technicians (bool, optional): Whether template is available to all technicians
            allowed_technician_roles (List[int], optional): List of technician role IDs that can use this template

        Returns:
            Dict: Updated document template
        """
        data = {}
        
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if mandatory is not None:
            data["mandatory"] = mandatory
        if fields is not None:
            if not isinstance(fields, list):
                raise ValueError("fields must be a list of dictionaries")
            # Process each field to remove None values
            processed_fields = []
            for field in fields:
                if not isinstance(field, dict):
                    raise ValueError("Each field must be a dictionary")
                processed_field = {k: v for k, v in field.items() if v is not None}
                processed_fields.append(processed_field)
            data["fields"] = processed_fields
        if available_to_all_technicians is not None:
            data["availableToAllTechnicians"] = available_to_all_technicians
        if allowed_technician_roles is not None:
            if not isinstance(allowed_technician_roles, list):
                raise ValueError("allowed_technician_roles must be a list of integers")
            data["allowedTechnicianRoles"] = allowed_technician_roles

        return self._request('PUT', f'/v2/templates/{template_id}', json=data) 

    def get_all_organization_documents(
        self,
        group_by: Optional[Literal["TEMPLATE", "ORGANIZATION"]] = None,
        organization_ids: Optional[str] = None,
        template_ids: Optional[str] = None,
        template_name: Optional[str] = None,
        document_name: Optional[str] = None
    ) -> List[Dict]:
        """
        List all organization documents with field values.

        Args:
            group_by (Literal["TEMPLATE", "ORGANIZATION"], optional): Group results by template or organization
            organization_ids (str, optional): Filter by organization IDs (comma-separated)
            template_ids (str, optional): Filter by template IDs (comma-separated)
            template_name (str, optional): Filter by template name
            document_name (str, optional): Filter by document name

        Returns:
            List[Dict]: List of organization documents containing:
                - documentId (int): Document identifier
                - documentName (str): Document name
                - documentDescription (str): Document description
                - documentUpdateTime (float): Document last updated
                - fields (List[Dict]): List of fields with:
                    - name (str): Field name
                    - value (Any): Field value
                    - valueUpdateTime (float): Field value last updated
                - documentTemplateId (int): Document template identifier
                - documentTemplateName (str): Document template name
                - organizationId (int): Organization identifier
        """
        params = {}
        if group_by is not None:
            if group_by not in ("TEMPLATE", "ORGANIZATION"):
                raise ValueError("group_by must be either 'TEMPLATE' or 'ORGANIZATION'")
            params["groupBy"] = group_by
        if organization_ids is not None:
            params["organizationIds"] = organization_ids
        if template_ids is not None:
            params["templateIds"] = template_ids
        if template_name is not None:
            params["templateName"] = template_name
        if document_name is not None:
            params["documentName"] = document_name

        return self._request('GET', '/v2/organization/documents', params=params) 

    def get_organization_documents(self, org_id: int) -> List[Dict]:
        """
        List organization documents with field values.

        Args:
            org_id (int): Organization identifier

        Returns:
            List[Dict]: List of organization documents containing:
                - documentId (int): Document identifier
                - documentName (str): Document name
                - documentDescription (str): Document description
                - documentUpdateTime (float): Document last updated
                - fields (List[Dict]): List of fields with:
                    - name (str): Field name
                    - value (Any): Field value
                    - valueUpdateTime (float): Field value last updated
                - documentTemplateId (int): Document template identifier
                - documentTemplateName (str): Document template name
                - organizationId (int): Organization identifier
        """
        return self._request('GET', f'/v2/organization/{org_id}/documents')

    def update_organization_document_by_id(
        self,
        org_id: int,
        document_id: int,
        document_name: Optional[str] = None,
        document_description: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Update an organization document by ID and return the updated version.

        Args:
            org_id (int): Organization identifier
            document_id (int): Organization document identifier
            document_name (str, optional): Document name
            document_description (str, optional): Document description
            fields (Dict[str, Any], optional): Document fields as key-value pairs

        Returns:
            Dict: Updated organization document containing:
                - documentId (int): Document identifier
                - documentName (str): Document name
                - documentDescription (str): Document description
                - documentUpdateTime (float): Document last updated
                - updatedFields (List[Dict]): List of updated fields with:
                    - name (str): Field name
                    - value (Any): Field value
                    - valueUpdateTime (float): Field value last updated
                - documentTemplateId (int): Document template identifier
                - documentTemplateName (str): Document template name
                - organizationId (int): Organization identifier
        """
        data = {}
        if document_name is not None:
            data["documentName"] = document_name
        if document_description is not None:
            data["documentDescription"] = document_description
        if fields is not None:
            if not isinstance(fields, dict):
                raise ValueError("fields must be a dictionary")
            # Remove None values from fields
            data["fields"] = {k: v for k, v in fields.items() if v is not None}

        return self._request('POST', f'/v2/organization/{org_id}/document/{document_id}', json=data) 

    def create_location_edf_document(self, json_data, org_id):
        """
        Create a location EDF document from MongoDB JSON data.
        
        Args:
            json_data (List[Dict]): Location EDF data from MongoDB
            org_id (int): Organization identifier
            
        Returns:
            Dict: Document formatted for the NinjaRMM API with fields:
                - documentName: "Onboarding-Locations"
                - documentDescription: "Onboarding-Locations"
                - fields: Mapped fields from EDF data
                - documentTemplateId: 23
                - organizationId: org_id
                - locationName: Location name
        """
        # Get the first record to extract common location info
        first_record = json_data[0]
        
        # Initialize fields dictionary with required field structure
        fields = {
            "organization": org_id,
            "location": first_record['Name'],  # Location name from the first record
            "locations": [first_record['Name']],  # Array of location names
            "remoteSupportOnly": False  # Default value
        }
        
        # Process security-specific fields
        for entry in json_data:
            if entry['Title'] == 'DNS Filter':
                # Convert 'Enabled'/'Disabled' to boolean
                fields['deployDnsfilter'] = entry['DropdownValue'] == 'Enabled'
                
            elif entry['Title'] == 'DNS Filter Software Key':
                fields['dnsfilterlocationkey'] = entry['TextFieldValue'] or None
                
            elif entry['Title'] == 'DefensX':
                # Convert 'Enabled'/'Disabled' to boolean
                fields['deployDefensx'] = entry['DropdownValue'] == 'Enabled'
                
            elif entry['Title'] == 'DefensX Software Key':
                fields['defensxlocationkey'] = entry['TextFieldValue'] or None
                
            # Map Remote Support fields
            elif entry['Title'] == 'Remote Servers' or entry['Title'] == 'Remote Workstations':
                if entry['CheckboxValue'] is True:
                    fields['remoteSupportOnly'] = True
        
        # Create the final document structure
        document = {
            "documentName": "Onboarding-Locations",
            "documentDescription": "Onboarding-Locations",
            "fields": fields,
            "documentTemplateId": 23,
            "organizationId": org_id,
            "locationName": first_record['Name']
        }
        
        return document 

    def register_document_template(self, template_id: int, name: str, field_mappings: Dict[str, Any]) -> None:
        """
        Register a new document template.
        
        Args:
            template_id (int): Template ID in NinjaRMM
            name (str): Template name
            field_mappings (Dict[str, Any]): Field mapping definitions
        """
        template = DocumentTemplate(template_id, name, field_mappings)
        self.template_registry.register_template(template)

    def prepare_document_body(
        self,
        input_data: Dict[str, Any],
        template_id: int,
        org_id: int
    ) -> Dict:
        """
        Create a document using a registered template.
        
        Args:
            input_data (Dict[str, Any]): Input JSON data containing the values to store
            template_id (int): The template ID to use
            org_id (int): Organization ID
            
        Returns:
            Dict: Created document
            
        Raises:
            ValueError: If template_id is not registered
        """
        from .document_templates import template_registry
        
        # Get template configuration
        template = template_registry.get_template_by_id(template_id)
        if template is None:
            raise ValueError(f"No template registered for template_id: {template_id}")
            
        # Transform data using template
        document_body = template.transform_data(input_data, org_id)
        
        # Create document
        return self.create_organization_document(
            organization_id=org_id,
            document_template_id=template_id,
            document_name=document_body["documentName"],
            document_description=document_body.get("documentDescription"),
            fields=document_body["fields"]
        )

class DocumentTemplate:
    """
    Class to define document templates and their field mappings.
    
    This class handles the mapping between input JSON data and NinjaRMM document fields.
    Each template defines how to transform input data into the expected document structure.
    """
    
    def __init__(self, template_id: int, name: str, field_mappings: Dict[str, Any]):
        """
        Initialize a document template.
        
        Args:
            template_id (int): The template ID in NinjaRMM
            name (str): Template name (e.g., "Onboarding-Organization", "Onboarding-Locations")
            field_mappings (Dict[str, Any]): Dictionary defining how to map input fields to document fields.
                Can include:
                - Direct field mappings (input_field: output_field)
                - Transform functions (input_field: transform_function)
                - Default values (field: default_value)
        """
        self.template_id = template_id
        self.name = name
        self.field_mappings = field_mappings
        
    def transform_data(self, input_data: Dict[str, Any], org_id: int) -> Dict[str, Any]:
        """
        Transform input data into the document format expected by NinjaRMM.
        
        Args:
            input_data (Dict[str, Any]): Input JSON data
            org_id (int): Organization ID
            
        Returns:
            Dict[str, Any]: Transformed document data in NinjaRMM format
        """
        fields = {}
        
        # Process each field mapping
        for input_field, mapping in self.field_mappings.items():
            if callable(mapping):
                # If mapping is a function, call it with the input value
                if input_field in input_data:
                    fields[input_field] = mapping(input_data[input_field])
            elif isinstance(mapping, dict) and 'default' in mapping:
                # If mapping has a default value
                fields[input_field] = input_data.get(input_field, mapping['default'])
            elif isinstance(mapping, str):
                # If mapping is a string (direct field mapping)
                if mapping in input_data:
                    fields[input_field] = input_data[mapping]
            else:
                # Use direct value from input if available
                if input_field in input_data:
                    fields[input_field] = input_data[input_field]
        
        # Create the document structure
        document = {
            "documentName": self.name,
            "documentDescription": self.name,
            "fields": fields,
            "documentTemplateId": self.template_id,
            "organizationId": org_id
        }
        
        # Add locationName if provided in input data
        if "locationName" in input_data:
            document["locationName"] = input_data["locationName"]
            
        return document

class DocumentTemplateRegistry:
    """
    Registry for document templates.
    Stores and manages available document templates.
    """
    
    def __init__(self):
        self._templates: Dict[int, DocumentTemplate] = {}
        
    def register_template(self, template: DocumentTemplate) -> None:
        """
        Register a new document template.
        
        Args:
            template (DocumentTemplate): Template to register
        """
        self._templates[template.template_id] = template
        
    def get_template(self, template_id: int) -> Optional[DocumentTemplate]:
        """
        Get a template by its ID.
        
        Args:
            template_id (int): Template ID to retrieve
            
        Returns:
            Optional[DocumentTemplate]: The template if found, None otherwise
        """
        return self._templates.get(template_id)
        
    def has_template(self, template_id: int) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_id (int): Template ID to check
            
        Returns:
            bool: True if template exists, False otherwise
        """
        return template_id in self._templates 
    