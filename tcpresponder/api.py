from fastapi import FastAPI, HTTPException
from db_manager import DatabaseManager, IPConfig
from pydantic import BaseModel
from typing import List, Optional
from cache_manager import HeartbeatCache
import pandas as pd
import mariadb
from sqlalchemy.engine import url as sa_url

app = FastAPI()
db_manager = DatabaseManager()
cache = HeartbeatCache()

# Extract connection parameters from SQLAlchemy engine
url = sa_url.make_url(db_manager.engine.url)
db_config = {
    'user': url.username,
    'password': url.password,
    'host': url.host,
    'port': url.port or 3306,
    'database': url.database,
    'pool_name': "heartbeat-pool",
    'pool_size': 8,
    'connect_timeout': 60
}

class IPConfigRequest(BaseModel):
    ip: str
    device_name: Optional[str] = ""
    push_url: Optional[str] = ""

@app.get("/")
async def root():
    return {"message": "TCP Responder API"}

@app.get("/heartbeats")
async def get_heartbeats():
    """Get heartbeat data from cache or database"""
    try:
        # Try to get data from cache first
        df = cache.get_data()
        if df is not None:
            return df.to_dict(orient='records')
        
        # If not in cache, get from database using MariaDB connector
        conn = mariadb.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT h.* 
                FROM heartbeat h
                JOIN monitor m ON h.monitor_id = m.id
            """)
            results = cursor.fetchall()
            df = pd.DataFrame(results)
            # Cache the data
            cache.set_data(df)
            return df.to_dict(orient='records')
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ip")
async def add_ip(ip_config: IPConfigRequest):
    """Add a new IP configuration"""
    try:
        db_manager.add_ip(IPConfig(
            ip_address=ip_config.ip,
            device_name=ip_config.device_name,
            client_name="",  # Will be updated by sync
            location_name="",  # Will be updated by sync
            is_static_ip=True,
            push_url=ip_config.push_url
        ))
        return {"message": f"Added IP {ip_config.ip}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ip")
async def get_ips():
    """Get all IP configurations"""
    try:
        return db_manager.get_all_ips()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ip/{ip}")
async def delete_ip(ip: str):
    """Delete an IP configuration"""
    try:
        db_manager.remove_ip(ip)
        return {"message": f"Deleted IP {ip}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_from_ninja():
    """Sync IPs from NinjaRMM"""
    try:
        ips = db_manager.sync_from_ninja()
        return {"message": f"Synced {len(ips)} IPs from NinjaRMM"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 