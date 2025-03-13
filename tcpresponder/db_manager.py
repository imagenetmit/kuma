from typing import List, Tuple
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import pymysql
from pymysql.cursors import DictCursor

load_dotenv()

UPTIME_KUMA_DB_TYPE = os.getenv("UPTIME_KUMA_DB_TYPE")
UPTIME_KUMA_DB_HOSTNAME = os.getenv("UPTIME_KUMA_DB_HOSTNAME")
UPTIME_KUMA_DB_PORT = os.getenv("UPTIME_KUMA_DB_PORT")
UPTIME_KUMA_DB_NAME = os.getenv("UPTIME_KUMA_DB_NAME")
UPTIME_KUMA_DB_USERNAME = os.getenv("UPTIME_KUMA_DB_USERNAME")
UPTIME_KUMA_DB_PASSWORD = os.getenv("UPTIME_KUMA_DB_PASSWORD")


@dataclass
class IPConfig:
    ip_address: str
    device_name: str
    client_name: str
    location_name: str
    is_static_ip: bool
    push_url: str

class DatabaseManager:
    def __init__(self):
        # MariaDB connection parameters
        self.db_config = {
            'host': UPTIME_KUMA_DB_HOSTNAME,
            'port': int(UPTIME_KUMA_DB_PORT) if UPTIME_KUMA_DB_PORT else 3306,
            'user': UPTIME_KUMA_DB_USERNAME,
            'password': UPTIME_KUMA_DB_PASSWORD,
            'database': UPTIME_KUMA_DB_NAME,
            'cursorclass': DictCursor
        }
        
        # Initialize the database if needed
        self.init_db()

    def get_connection(self):
        """Create and return a new database connection"""
        return pymysql.connect(**self.db_config)

    def init_db(self):
        """Initialize the database if the table doesn't exist"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS allowed_ips (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ip_address VARCHAR(45) UNIQUE NOT NULL,
                        device_name VARCHAR(255),
                        client_name VARCHAR(255) NOT NULL,
                        location_name VARCHAR(255) NOT NULL,
                        is_static_ip BOOLEAN NOT NULL,
                        push_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            conn.commit()
        finally:
            conn.close()

    def add_ip(self, ip_config: IPConfig):
        """Add or update an IP configuration in the database"""
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
                    ip_config.device_name,
                    ip_config.client_name,
                    ip_config.location_name,
                    ip_config.is_static_ip,
                    ip_config.push_url
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
                return result['push_url'] if result else None
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