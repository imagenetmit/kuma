import os
import asyncio
import multiprocessing
from fastapi import FastAPI
from api import app
from db_manager import DatabaseManager
from cache_manager import CacheSync
from tcp_monitor import TCPMonitor
from sqlalchemy import create_engine

def run_api():
    """Run the FastAPI server"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def run_cache_sync():
    """Run the cache sync service"""
    # Create SQLAlchemy engine for cache sync using MariaDB
    engine = create_engine(
        f"mysql+mariadb://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    cache_sync = CacheSync(engine)
    await cache_sync.start_sync()

async def run_tcp_monitor(db_manager: DatabaseManager):
    """Run the TCP monitor service"""
    monitor = TCPMonitor(db_manager=db_manager, port=50000)
    await monitor.start_server()

async def main():
    """Main application entry point"""
    # Initialize database manager
    db = DatabaseManager()
    
    # Start cache sync
    cache_sync_task = asyncio.create_task(run_cache_sync())
    
    # Start TCP monitor
    await run_tcp_monitor(db)
    
    # Cleanup
    cache_sync_task.cancel()
    try:
        await cache_sync_task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    # Start API server in a separate process
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()
    
    # Run TCP monitor and cache sync in the main process
    asyncio.run(main())