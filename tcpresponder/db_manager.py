from typing import List, Dict, Any
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import mariadb
import pandas as pd
from ninjapy.client import NinjaRMMClient
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

load_dotenv()

UPTIME_KUMA_DB_TYPE = os.getenv("UPTIME_KUMA_DB_TYPE")
UPTIME_KUMA_DB_HOSTNAME = os.getenv("UPTIME_KUMA_DB_HOSTNAME")
UPTIME_KUMA_DB_PORT = os.getenv("UPTIME_KUMA_DB_PORT")
UPTIME_KUMA_DB_NAME = os.getenv("UPTIME_KUMA_DB_NAME")
UPTIME_KUMA_DB_USERNAME = os.getenv("UPTIME_KUMA_DB_USERNAME")
UPTIME_KUMA_DB_PASSWORD = os.getenv("UPTIME_KUMA_DB_PASSWORD")

# Centralized database configuration
DB_CONFIG = {
    'host': UPTIME_KUMA_DB_HOSTNAME,
    'port': int(UPTIME_KUMA_DB_PORT or "3306"),
    'user': UPTIME_KUMA_DB_USERNAME,
    'password': UPTIME_KUMA_DB_PASSWORD,
    'database': UPTIME_KUMA_DB_NAME,
    'pool_name': "mariadb-pool",
    'pool_size': 8,
    'connect_timeout': 60
}

@dataclass
class IPConfig:
    ip_address: str
    is_static_ip: bool
    client_name: str = ""  # Default to empty string
    location_name: str = ""  # Default to empty string
    device_name: str = ""  # Default to empty string
    push_url: str = ""  # Default to empty string

class DatabaseManager:
    def __init__(self):
        # Create SQLAlchemy engine for cache sync using MariaDB with connection pooling
        self.engine = create_engine(
            f"mysql+mariadb://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
            poolclass=QueuePool,
            pool_size=DB_CONFIG['pool_size'],
            pool_timeout=DB_CONFIG['connect_timeout']
        )
        
        self.init_db()
        self.ninja = self._init_ninja_client()

    def _init_ninja_client(self) -> NinjaRMMClient:
        """Initialize NinjaRMM client"""
        return NinjaRMMClient(
            client_id=os.getenv("NINJA_CLIENT_ID"),
            client_secret=os.getenv("NINJA_CLIENT_SECRET"),
            token_url=os.getenv("NINJA_TOKEN_URL"),
            scope=os.getenv("NINJA_SCOPE")
        )

    def get_connection(self):
        """Create and return a new database connection"""
        conn = mariadb.connect(**DB_CONFIG)
        conn.autocommit = True  # Enable autocommit for better performance
        return conn

    def init_db(self):
        """Initialize the database if the table doesn't exist"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS allowed_ips (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ip_address VARCHAR(45) UNIQUE NOT NULL,
                        device_name VARCHAR(255) DEFAULT '',
                        client_name VARCHAR(255) NOT NULL,
                        location_name VARCHAR(255) NOT NULL,
                        is_static_ip BOOLEAN NOT NULL,
                        push_url TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            conn.commit()
        finally:
            conn.close()

    def sync_from_ninja(self) -> List[Dict[str, Any]]:
        """Sync IPs from NinjaRMM"""
        try:
            ninja_data = self.ninja.get_devices_detailed(expand='organization,location')
            df = pd.json_normalize(ninja_data)
            
            # Extract and clean data
            df = df[['references.organization.name', 'references.location.name', 'publicIP']]
            df = df.dropna()
            
            # Group and count IPs
            ip_counts = df.groupby(['references.organization.name', 'references.location.name', 'publicIP']).size()
            ip_counts = ip_counts.reset_index(name='count')
            ip_counts = ip_counts.sort_values(['references.organization.name', 'count'], ascending=[True, False])
            
            # Convert to IPConfig objects and add to database
            for _, row in ip_counts.iterrows():
                ip_config = IPConfig(
                    ip_address=row['publicIP'],
                    client_name=row['references.organization.name'],
                    location_name=row['references.location.name'],
                    is_static_ip=True
                )
                self.add_ip(ip_config)
            
            return ip_counts.to_dict(orient='records')
        except Exception as e:
            print(f"Error syncing from NinjaRMM: {e}")
            return []

    def add_ip(self, ip_config: IPConfig):
        """Add or update an IP configuration"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO allowed_ips 
                    (ip_address, device_name, client_name, location_name, is_static_ip, push_url)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    device_name = VALUES(device_name),
                    client_name = VALUES(client_name),
                    location_name = VALUES(location_name),
                    is_static_ip = VALUES(is_static_ip),
                    push_url = VALUES(push_url)
                ''', (
                    ip_config.ip_address,
                    ip_config.device_name or "",
                    ip_config.client_name,
                    ip_config.location_name,
                    ip_config.is_static_ip,
                    ip_config.push_url or ""
                ))
            conn.commit()
        finally:
            conn.close()

    def remove_ip(self, ip_address: str):
        """Remove an IP address from the allowed list"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM allowed_ips WHERE ip_address = %s", (ip_address,))
            conn.commit()
        finally:
            conn.close()

    def get_all_ips(self) -> List[IPConfig]:
        """Get all allowed IP configurations"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT ip_address, device_name, client_name, location_name, 
                           is_static_ip, push_url 
                    FROM allowed_ips
                ''')
                rows = cursor.fetchall()
                return [IPConfig(**row) for row in rows]
        finally:
            conn.close()

    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if an IP address is in the allowed list"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM allowed_ips WHERE ip_address = %s", (ip_address,))
                return cursor.fetchone() is not None
        finally:
            conn.close()

    def get_webhook_url(self, ip_address: str) -> str:
        """Get the webhook URL for an IP address"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT push_url FROM allowed_ips WHERE ip_address = %s", (ip_address,))
                result = cursor.fetchone()
                return result['push_url'] if result else ""
        finally:
            conn.close()

    def get_ip_details(self, ip_address: str) -> IPConfig:
        """Get detailed information about an allowed IP"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT ip_address, device_name, client_name, location_name, 
                           is_static_ip, push_url 
                    FROM allowed_ips 
                    WHERE ip_address = %s
                ''', (ip_address,))
                row = cursor.fetchone()
                return IPConfig(**row) if row else None
        finally:
            conn.close() 