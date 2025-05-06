import pytest
from unittest.mock import Mock, patch, AsyncMock
from sync_service import BinlogSyncService
from pymysqlreplication.row_event import WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent
import logging

@pytest.fixture
def binlog_sync():
    """Create a test binlog sync service"""
    with patch('sync_service.HeartbeatCache') as mock_cache:
        mock_cache_instance = Mock()
        mock_cache.return_value = mock_cache_instance
        return BinlogSyncService(mock_cache_instance)

def test_init(binlog_sync):
    """Test initialization of binlog sync service"""
    assert binlog_sync.running is False
    assert binlog_sync.stream is None
    assert 'host' in binlog_sync.binlog_config
    assert 'port' in binlog_sync.binlog_config
    assert 'user' in binlog_sync.binlog_config
    assert 'passwd' in binlog_sync.binlog_config
    assert 'db' in binlog_sync.binlog_config

def test_stop(binlog_sync):
    """Test stopping the binlog sync service"""
    mock_stream = Mock()
    binlog_sync.stream = mock_stream
    binlog_sync.running = True
    
    binlog_sync.stop()
    
    assert binlog_sync.running is False
    assert binlog_sync.stream is None
    mock_stream.close.assert_called_once()

@pytest.mark.asyncio
async def test_start_stop(binlog_sync):
    """Test starting and stopping the binlog sync service"""
    with patch('sync_service.BinLogStreamReader') as mock_reader:
        mock_stream = Mock()
        mock_reader.return_value = mock_stream
        mock_stream.__iter__.return_value = []  # Empty stream
        
        # Start service in background
        import asyncio
        task = asyncio.create_task(binlog_sync.start())
        
        # Let it run for a moment
        await asyncio.sleep(0)
        assert binlog_sync.running is True
        
        # Stop service
        binlog_sync.stop()
        await task
        
        # Verify stream was created with correct parameters
        mock_reader.assert_called_once()
        call_args = mock_reader.call_args[1]
        assert call_args['connection_settings'] == binlog_sync.binlog_config
        assert call_args['server_id'] == 100
        assert call_args['only_events'] == [WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent]
        assert call_args['only_tables'] == ['heartbeat']

@pytest.mark.asyncio
async def test_handle_events(binlog_sync):
    """Test handling of binlog events"""
    with patch('sync_service.BinLogStreamReader') as mock_reader:
        # Create mock events
        mock_write_event = Mock(spec=WriteRowsEvent)
        mock_update_event = Mock(spec=UpdateRowsEvent)
        mock_delete_event = Mock(spec=DeleteRowsEvent)
        
        mock_stream = Mock()
        mock_reader.return_value = mock_stream
        mock_stream.__iter__.return_value = [
            mock_write_event,
            mock_update_event,
            mock_delete_event
        ]
        
        # Start service in background
        import asyncio
        task = asyncio.create_task(binlog_sync.start())
        
        # Let it run for a moment
        await asyncio.sleep(0)
        
        # Stop service
        binlog_sync.stop()
        await task
        
        # Verify cache was invalidated for each event
        assert binlog_sync.cache.invalidate.call_count == 3

@pytest.mark.asyncio
async def test_error_handling(binlog_sync, caplog):
    """Test error handling in binlog sync service"""
    with patch('sync_service.BinLogStreamReader') as mock_reader:
        # Make reader raise an exception
        mock_reader.side_effect = Exception("Test error")
        
        # Start service in background
        import asyncio
        task = asyncio.create_task(binlog_sync.start())
        
        # Let it run for a moment
        await asyncio.sleep(0)
        
        # Stop service
        binlog_sync.stop()
        await task
        
        # Verify error was logged
        assert "Error in binlog sync service: Test error" in caplog.text 