import sqlite3
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class IPConfig:
    ip_address: str
    device_name: str
    client_name: str
    location_name: str
    is_static_ip: bool
    push_url: str

class DatabaseManager:
    def __init__(self, db_path: str = "./data/tcp_monitor.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS allowed_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    device_name TEXT,
                    client_name TEXT NOT NULL,
                    location_name TEXT NOT NULL,
                    is_static_ip BOOLEAN NOT NULL,
                    push_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def add_ip(self, ip_config: IPConfig):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO allowed_ips 
                (ip_address, device_name, client_name, location_name, is_static_ip, push_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                ip_config.ip_address,
                ip_config.device_name,
                ip_config.client_name,
                ip_config.location_name,
                ip_config.is_static_ip,
                ip_config.push_url
            ))
            conn.commit()

    def remove_ip(self, ip_address: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM allowed_ips WHERE ip_address = ?", (ip_address,))
            conn.commit()

    def get_all_ips(self) -> List[IPConfig]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ip_address, device_name, client_name, location_name, 
                       is_static_ip, push_url 
                FROM allowed_ips
            ''')
            rows = cursor.fetchall()
            return [IPConfig(**dict(row)) for row in rows]

    def is_ip_allowed(self, ip_address: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM allowed_ips WHERE ip_address = ?", (ip_address,))
            return cursor.fetchone() is not None

    def get_webhook_url(self, ip_address: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT push_url FROM allowed_ips WHERE ip_address = ?", (ip_address,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_ip_details(self, ip_address: str) -> IPConfig:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ip_address, device_name, client_name, location_name, 
                       is_static_ip, push_url 
                FROM allowed_ips 
                WHERE ip_address = ?
            ''', (ip_address,))
            row = cursor.fetchone()
            return IPConfig(**dict(row)) if row else None 