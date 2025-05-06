import pytest
from db_manager import IPConfig, DatabaseManager
from unittest.mock import Mock, patch

@pytest.fixture
def db_manager():
    """Create a test database manager with mocked connections"""
    manager = DatabaseManager()
    # Mock the database connection and cursor
    mock_cursor = Mock()
    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor
    manager.get_connection = Mock(return_value=mock_conn)
    return manager

def test_add_ip(db_manager):
    """Test adding an IP configuration"""
    ip_config = IPConfig(
        ip_address="192.168.1.1",
        is_static_ip=True,
        client_name="test_client",
        location_name="test_location",
        device_name="test_device",
        push_url="http://test.com"
    )
    
    db_manager.add_ip(ip_config)
    
    # Verify the SQL query was executed with correct parameters
    cursor = db_manager.get_connection().cursor()
    # Get the last call to execute (ignoring table creation)
    last_call = cursor.execute.call_args_list[-1]
    assert "INSERT INTO allowed_ips" in last_call[0][0]
    assert last_call[0][1] == (
        "192.168.1.1",
        "test_device",
        "test_client",
        "test_location",
        True,
        "http://test.com"
    )

def test_get_all_ips(db_manager):
    """Test retrieving all IP configurations"""
    # Mock the database response
    mock_rows = [
        {
            'ip_address': '192.168.1.1',
            'device_name': 'test_device',
            'client_name': 'test_client',
            'location_name': 'test_location',
            'is_static_ip': True,
            'push_url': 'http://test.com'
        }
    ]
    db_manager.get_connection().cursor().fetchall.return_value = mock_rows
    
    result = db_manager.get_all_ips()
    
    assert len(result) == 1
    assert isinstance(result[0], IPConfig)
    assert result[0].ip_address == '192.168.1.1'
    assert result[0].device_name == 'test_device'
    assert result[0].client_name == 'test_client'
    assert result[0].location_name == 'test_location'
    assert result[0].is_static_ip is True
    assert result[0].push_url == 'http://test.com'

def test_remove_ip(db_manager):
    """Test removing an IP configuration"""
    ip_address = "192.168.1.1"
    
    db_manager.remove_ip(ip_address)
    
    # Verify the SQL query was executed with correct parameters
    cursor = db_manager.get_connection().cursor()
    # Get the last call to execute (ignoring table creation)
    last_call = cursor.execute.call_args_list[-1]
    assert "DELETE FROM allowed_ips" in last_call[0][0]
    assert last_call[0][1] == (ip_address,)

def test_get_webhook_url(db_manager):
    """Test getting webhook URL for an IP"""
    ip_address = "192.168.1.1"
    mock_result = {'push_url': 'http://test.com'}
    db_manager.get_connection().cursor().fetchone.return_value = mock_result
    
    result = db_manager.get_webhook_url(ip_address)
    
    assert result == 'http://test.com'
    cursor = db_manager.get_connection().cursor()
    last_call = cursor.execute.call_args_list[-1]
    assert "SELECT push_url FROM allowed_ips" in last_call[0][0]
    assert last_call[0][1] == (ip_address,)

def test_get_webhook_url_not_found(db_manager):
    """Test getting webhook URL for non-existent IP"""
    ip_address = "192.168.1.1"
    db_manager.get_connection().cursor().fetchone.return_value = None
    
    result = db_manager.get_webhook_url(ip_address)
    
    assert result == "" 