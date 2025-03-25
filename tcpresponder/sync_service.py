import os
import time
import logging
from typing import Optional
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    WriteRowsEvent,
    UpdateRowsEvent,
    DeleteRowsEvent
)
from cache_manager import HeartbeatCache
from db_manager import DB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_service.log'),
        logging.StreamHandler()
    ]
)

class BinlogSyncService:
    """
    Service that monitors MariaDB binlog for changes to the heartbeat table
    and invalidates the cache when changes are detected.
    
    This service uses MariaDB's binary log replication to track changes
    to the heartbeat table in real-time, ensuring cache consistency.
    """
    
    def __init__(self, cache: Optional[HeartbeatCache] = None):
        """
        Initialize the binlog sync service.
        
        Args:
            cache: Optional HeartbeatCache instance. If not provided, a new one will be created.
        """
        self.cache = cache or HeartbeatCache()
        self.running = False
        self.stream: Optional[BinLogStreamReader] = None
        
        # Convert DB_CONFIG to pymysqlreplication format
        self.binlog_config = {
            'host': DB_CONFIG['host'],
            'port': DB_CONFIG['port'],
            'user': DB_CONFIG['user'],
            'passwd': DB_CONFIG['password'],
            'db': DB_CONFIG['database']
        }

    def start(self):
        """Start the binlog sync service."""
        self.running = True
        logging.info("Starting binlog sync service...")
        
        while self.running:
            try:
                self.stream = BinLogStreamReader(
                    connection_settings=self.binlog_config,
                    server_id=100,  # Unique server ID for this replica
                    only_events=[WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent],
                    only_tables=['heartbeat']
                )

                for binlogevent in self.stream:
                    if not self.running:
                        break
                        
                    logging.info(f"Detected {binlogevent.__class__.__name__} on heartbeat table")
                    self.cache.invalidate()
                    
                if self.running:
                    logging.warning("Binlog stream ended, attempting to reconnect...")
                    time.sleep(5)  # Wait before reconnecting
                    
            except Exception as e:
                logging.error(f"Error in binlog sync service: {e}")
                if self.running:
                    time.sleep(5)  # Wait before retry
            finally:
                if self.stream:
                    self.stream.close()
                    self.stream = None

    def stop(self):
        """Stop the binlog sync service gracefully."""
        logging.info("Stopping binlog sync service...")
        self.running = False
        if self.stream:
            self.stream.close()
            self.stream = None

def main():
    """Main entry point for the sync service."""
    # Wait for services to be ready
    logging.info("Waiting for services to be ready...")
    time.sleep(10)
    
    service = BinlogSyncService()
    try:
        service.start()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
    finally:
        service.stop()

if __name__ == "__main__":
    main() 