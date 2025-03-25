import redis
import pickle
import pandas as pd
import mariadb
import os
import asyncio
from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.engine import url as sa_url
from db_manager import DB_CONFIG

class HeartbeatCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=False
        )
        self.CACHE_KEY = 'heartbeat_data'
        self.LAST_UPDATE_KEY = 'heartbeat_last_update'
        self.CACHE_TTL = 300  # 5 minutes

    def get_data(self) -> Optional[pd.DataFrame]:
        """Get heartbeat data from cache or database"""
        cached_data = self.redis_client.get(self.CACHE_KEY)
        if cached_data:
            return pickle.loads(cached_data)
        return None

    def set_data(self, df: pd.DataFrame) -> None:
        """Cache heartbeat data"""
        self.redis_client.setex(
            self.CACHE_KEY,
            self.CACHE_TTL,
            pickle.dumps(df)
        )
        self.redis_client.set(
            self.LAST_UPDATE_KEY,
            datetime.now().timestamp()
        )

    def get_last_update(self) -> Optional[float]:
        """Get timestamp of last update"""
        last_update = self.redis_client.get(self.LAST_UPDATE_KEY)
        return float(last_update) if last_update else None

    def invalidate(self) -> None:
        """Invalidate the cache"""
        self.redis_client.delete(self.CACHE_KEY)
        self.redis_client.delete(self.LAST_UPDATE_KEY)

class CacheSync:
    def __init__(self, engine):
        self.engine = engine
        self.cache = HeartbeatCache()
        self.running = False
        self.poll_interval = 5  # seconds

    async def check_for_updates(self):
        """Check if heartbeat data has been updated"""
        try:
            conn = mariadb.connect(**DB_CONFIG)
            conn.autocommit = True
            cursor = conn.cursor(dictionary=True)
            
            try:
                # Get last update time from heartbeat table
                cursor.execute("""
                    SELECT MAX(updated_at) as last_update
                    FROM heartbeat
                """)
                last_db_update = cursor.fetchone()['last_update']
                
                if last_db_update:
                    last_cache_update = self.cache.get_last_update()
                    if not last_cache_update or last_db_update.timestamp() > last_cache_update:
                        # Data has been updated, refresh cache
                        cursor.execute("""
                            SELECT h.* 
                            FROM heartbeat h
                            JOIN monitor m ON h.monitor_id = m.id
                        """)
                        results = cursor.fetchall()
                        df = pd.DataFrame(results)
                        self.cache.set_data(df)
                        print("Cache updated with new heartbeat data")
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            print(f"Error checking for updates: {e}")

    async def start_sync(self):
        """Start the cache sync process"""
        self.running = True
        print("Starting cache sync service...")
        
        while self.running:
            try:
                await self.check_for_updates()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                print(f"Error in cache sync: {e}")
                await asyncio.sleep(5)  # Wait before retry

    def stop_sync(self):
        """Stop the cache sync process"""
        self.running = False
        print("Stopping cache sync service...") 