"""
NinjaRMM document templates configuration.
This module contains template definitions and handling for various document types in NinjaRMM.
"""

from typing import Dict, Any, List, Optional, Union


class DocumentTemplate:
    """Class representing a document template with field mapping functionality."""
    
    def __init__(self, template_id: int, name: str, field_mappings: Dict[str, Any]):
        """
        Initialize a document template.
        
        Args:
            template_id: The template ID in NinjaRMM
            name: Template name
            field_mappings: Dictionary defining how to map input fields to document fields
        """
        self.template_id = template_id
        self.name = name
        self.field_mappings = field_mappings

    def transform_data(self, input_data: Union[Dict[str, Any], List[Dict[str, Any]]], org_id: int) -> List[Dict[str, Any]]:
        """
        Transform input data into the document format expected by NinjaRMM.
        Creates a separate document for each location.
        
        Args:
            input_data: Input data to transform. Can be a single location or multiple locations.
            org_id: Organization ID
            
        Returns:
            List of transformed document data in NinjaRMM format, one per location
        """
        # Ensure input_data is a list
        if isinstance(input_data, dict):
            input_data = [input_data]
            
        # Group data by location
        location_data = {}
        for item in input_data:
            if 'Name' in item:
                location_name = item['Name']
                if location_name not in location_data:
                    location_data[location_name] = []
                location_data[location_name].append(item)
        
        documents = []
        # Create a separate document for each location
        for location_name, location_items in location_data.items():
            fields = {}
            
            # Process each field mapping for this location's data
            for field_name, mapping in self.field_mappings.items():
                if callable(mapping):
                    fields[field_name] = mapping(location_items)
            
            # Create the document structure for this location
            document = {
                "documentName": f"{location_name}",  # Just use the location name
                "documentDescription": self.name,
                "fields": fields,
                "documentTemplateId": self.template_id,
                "organizationId": org_id
            }
            
            documents.append(document)
        
        return documents


class DocumentFieldMapper:
    """Base class for document field mapping functions."""
    
    @staticmethod
    def create_location_entity(org_id: int) -> Dict[str, Any]:
        """Create a location entity structure."""
        return {
            "entityId": org_id,
            "type": "CLIENT_LOCATION"
        }

    @staticmethod
    def map_remote_support(data: List[Dict[str, Any]]) -> bool:
        """Check if either Remote Servers or Remote Workstations is True for this location."""
        for item in data:
            if item['Title'] in ['Remote Servers', 'Remote Workstations']:
                if item.get('CheckboxValue', False):
                    return True
        return False

    @staticmethod
    def map_dns_filter(data: List[Dict[str, Any]]) -> bool:
        """Map DNS Filter enabled/disabled state for this location."""
        for item in data:
            if item['Title'] == 'DNS Filter':
                return item.get('DropdownValue') == 'Enabled'
        return False

    @staticmethod
    def map_dns_key(data: List[Dict[str, Any]]) -> Optional[str]:
        """Extract DNS Filter software key for this location."""
        for item in data:
            if item['Title'] == 'DNS Filter Software Key':
                return item.get('TextFieldValue') or None
        return None

    @staticmethod
    def map_defensx(data: List[Dict[str, Any]]) -> bool:
        """Map DefensX enabled/disabled state for this location."""
        for item in data:
            if item['Title'] == 'DefensX':
                return item.get('DropdownValue') == 'Enabled'
        return False

    @staticmethod
    def map_defensx_key(data: List[Dict[str, Any]]) -> Optional[str]:
        """Extract DefensX software key for this location."""
        for item in data:
            if item['Title'] == 'DefensX Software Key':
                return item.get('TextFieldValue') or None
        return None

    @staticmethod
    def map_location_name(data: List[Dict[str, Any]]) -> str:
        """Get location name."""
        for item in data:
            if 'Name' in item:
                return item['Name']
        return ""

    @staticmethod
    def map_remote_servers(data: List[Dict[str, Any]]) -> bool:
        """Get remote servers status for this location."""
        for item in data:
            if item['Title'] == 'Remote Servers':
                return item.get('CheckboxValue', False)
        return False

    @staticmethod
    def map_remote_workstations(data: List[Dict[str, Any]]) -> bool:
        """Get remote workstations status for this location."""
        for item in data:
            if item['Title'] == 'Remote Workstations':
                return item.get('CheckboxValue', False)
        return False


class TemplateRegistry:
    """Registry of all document templates."""
    
    def __init__(self):
        self.templates: Dict[str, DocumentTemplate] = {}
        self._init_templates()
    
    def _init_templates(self):
        """Initialize all available templates."""
        self._init_onboarding_locations()
        # Add more template initializations here as needed
        # self._init_template_name()
    
    def _init_onboarding_locations(self):
        """Initialize the Onboarding-Locations template."""
        mapper = DocumentFieldMapper()
        
        template = DocumentTemplate(
            template_id=23,
            name="Onboarding-Locations",
            field_mappings={
                "location": lambda data: mapper.create_location_entity(data[0]['locationid_ninja']),
                "remoteSupportOnly": mapper.map_remote_support,
                "remoteservers": mapper.map_remote_servers,
                "remoteworkstations": mapper.map_remote_workstations,
                "deployDnsfilter": mapper.map_dns_filter,
                "dnsfilterlocationkey": mapper.map_dns_key,
                "deployDefensx": mapper.map_defensx,
                "defensxlocationkey": mapper.map_defensx_key
            }
        )
        
        self.templates["onboarding_locations"] = template
    
    def get_template(self, template_name: str) -> DocumentTemplate:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template instance
            
        Raises:
            KeyError: If template_name is not found
        """
        return self.templates[template_name]
    
    def get_template_by_id(self, template_id: int) -> Optional[DocumentTemplate]:
        """
        Get a template by its ID.
        
        Args:
            template_id: Template ID to retrieve
            
        Returns:
            Template instance if found, None otherwise
        """
        for template in self.templates.values():
            if template.template_id == template_id:
                return template
        return None


# Global instance of template registry
template_registry = TemplateRegistry() 