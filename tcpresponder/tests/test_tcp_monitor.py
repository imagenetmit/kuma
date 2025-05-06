import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from tcp_monitor import TCPMonitor
from db_manager import DatabaseManager

@pytest.fixture
def db_manager():
    """Create a mock database manager"""
    return Mock(spec=DatabaseManager)

@pytest.fixture
def tcp_monitor(db_manager):
    """Create a test TCP monitor"""
    return TCPMonitor(db_manager=db_manager, port=50000)

@pytest.mark.asyncio
async def test_handle_connection(tcp_monitor):
    """Test handling a TCP connection"""
    # Create mock reader and writer
    reader = AsyncMock()
    writer = AsyncMock()
    writer.get_extra_info.return_value = ('192.168.1.1', 12345)
    
    # Mock NinjaRMM client response
    with patch('tcp_monitor.ninja') as mock_ninja:
        mock_ninja.search_devices.return_value = {
            'devices': [{
                'references': {
                    'location': {'name': 'test_location'},
                    'organization': {'name': 'test_org'}
                }
            }]
        }
        
        # Mock webhook URL
        tcp_monitor.db_manager.get_webhook_url.return_value = 'http://test.com'
        
        # Mock aiohttp client session
        with patch('tcp_monitor.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # Mock get_extra_info to return a tuple directly
            writer.get_extra_info = Mock(return_value=('192.168.1.1', 12345))
            
            # Mock writer methods
            writer.close = AsyncMock()
            writer.wait_closed = AsyncMock()
            
            await tcp_monitor.handle_connection(reader, writer)
            
            # Verify connection was processed
            writer.close.assert_called_once()
            writer.wait_closed.assert_called_once()

@pytest.mark.asyncio
async def test_send_webhook_success(tcp_monitor):
    """Test successful webhook sending"""
    # Mock webhook URL
    tcp_monitor.db_manager.get_webhook_url.return_value = 'http://test.com'
    
    # Mock aiohttp client session
    with patch('tcp_monitor.aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        await tcp_monitor.send_webhook('192.168.1.1')
        
        # Verify webhook was sent
        mock_session.return_value.__aenter__.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_send_webhook_failure(tcp_monitor):
    """Test webhook sending failure"""
    # Mock webhook URL
    tcp_monitor.db_manager.get_webhook_url.return_value = 'http://test.com'
    
    # Mock aiohttp client session with error
    with patch('tcp_monitor.aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.get.side_effect = Exception('Test error')
        
        await tcp_monitor.send_webhook('192.168.1.1')
        
        # Verify error was handled gracefully
        mock_session.return_value.__aenter__.return_value.get.assert_called_once()

@pytest.mark.asyncio
async def test_send_webhook_no_url(tcp_monitor):
    """Test webhook sending when no URL is available"""
    # Mock no webhook URL
    tcp_monitor.db_manager.get_webhook_url.return_value = ''
    
    await tcp_monitor.send_webhook('192.168.1.1')
    
    # Verify webhook URL was checked but not sent
    tcp_monitor.db_manager.get_webhook_url.assert_called_once_with('192.168.1.1')

@pytest.mark.asyncio
async def test_start_server(tcp_monitor):
    """Test server startup"""
    with patch('asyncio.start_server') as mock_start_server:
        mock_server = AsyncMock()
        mock_start_server.return_value = mock_server
        
        # Start server
        await tcp_monitor.start_server()
        
        # Verify server was started
        mock_start_server.assert_called_once()
        mock_server.serve_forever.assert_called_once() 