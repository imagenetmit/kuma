import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import pandas as pd
import pickle
from cache_manager import HeartbeatCache, CacheSync
import asyncio

@pytest.fixture
def redis_mock():
    """Create a mock Redis client"""
    with patch('cache_manager.redis.Redis') as mock_redis:
        mock_client = Mock()
        mock_redis.return_value = mock_client
        yield mock_client

@pytest.fixture
def heartbeat_cache(redis_mock):
    """Create a test heartbeat cache"""
    return HeartbeatCache()

@pytest.fixture
def cache_sync():
    """Create a test cache sync service"""
    with patch('cache_manager.create_engine') as mock_engine:
        mock_engine.return_value = Mock()
        return CacheSync(mock_engine.return_value)

def test_cache_set_get(heartbeat_cache, redis_mock):
    """Test setting and getting data from cache"""
    # Test data
    test_df = pd.DataFrame({'test': [1, 2, 3]})
    
    # Set data
    heartbeat_cache.set_data(test_df)
    
    # Verify Redis was called correctly
    redis_mock.setex.assert_called_once()
    assert redis_mock.setex.call_args[0][0] == heartbeat_cache.CACHE_KEY
    assert redis_mock.setex.call_args[0][1] == heartbeat_cache.CACHE_TTL
    
    # Mock get response with pickled DataFrame
    pickled_df = pickle.dumps(test_df)
    redis_mock.get.return_value = pickled_df
    
    # Get data
    result = heartbeat_cache.get_data()
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3

def test_cache_invalidate(heartbeat_cache, redis_mock):
    """Test cache invalidation"""
    heartbeat_cache.invalidate()
    
    # Verify both keys were deleted
    assert redis_mock.delete.call_count == 2
    delete_calls = redis_mock.delete.call_args_list
    delete_keys = [call[0][0] for call in delete_calls]
    assert heartbeat_cache.CACHE_KEY in delete_keys
    assert heartbeat_cache.LAST_UPDATE_KEY in delete_keys

def test_cache_last_update(heartbeat_cache, redis_mock):
    """Test last update timestamp handling"""
    # Test timestamp
    test_timestamp = datetime.now().timestamp()
    redis_mock.get.return_value = str(test_timestamp)
    
    result = heartbeat_cache.get_last_update()
    
    assert result == test_timestamp

@pytest.mark.asyncio
async def test_cache_sync_start_stop(cache_sync, monkeypatch):
    """Test cache sync service start and stop"""
    # Mock asyncio.sleep to avoid actual delays
    async def mock_sleep(*args):
        if not cache_sync.running:
            raise asyncio.CancelledError()
    monkeypatch.setattr(asyncio, 'sleep', mock_sleep)
    
    # Mock check_for_updates to avoid database calls
    cache_sync.check_for_updates = AsyncMock()
    
    # Start sync in background task
    task = asyncio.create_task(cache_sync.start_sync())
    
    # Let it run for a moment
    await asyncio.sleep(0)
    assert cache_sync.running is True
    
    # Stop sync
    cache_sync.stop_sync()
    await task
    assert cache_sync.running is False
    
    # Verify check_for_updates was called
    assert cache_sync.check_for_updates.called

@pytest.mark.asyncio
async def test_cache_sync_check_updates(cache_sync):
    """Test cache sync update checking"""
    with patch('cache_manager.mariadb.connect') as mock_connect:
        # Setup mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock database responses
        current_time = datetime.now()
        mock_cursor.fetchone.return_value = {'last_update': current_time}
        mock_cursor.fetchall.return_value = [
            {'monitor_id': 1, 'status': 'up', 'time': current_time},
            {'monitor_id': 2, 'status': 'down', 'time': current_time}
        ]
        
        # Mock cache last update to be older
        cache_sync.cache.get_last_update = Mock(return_value=current_time.timestamp() - 3600)
        
        await cache_sync.check_for_updates()
        
        # Verify database queries
        assert mock_cursor.execute.call_count == 2
        queries = [call[0][0] for call in mock_cursor.execute.call_args_list]
        assert any("SELECT MAX(updated_at)" in query for query in queries)
        assert any("SELECT h.*" in query for query in queries)
        
        # Verify cursor and connection were closed
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once() 