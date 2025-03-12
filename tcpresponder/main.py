import asyncio
import uvicorn
import requests
from ninjapy.client import NinjaRMMClient
from tcp_monitor import TCPMonitor
from db_manager import DatabaseManager, IPConfig
from populate_db import retrieve_all_ips
from api import app
import os
from dotenv import load_dotenv
import multiprocessing

load_dotenv()

# Initialize database and add IPs
db_manager = DatabaseManager()

NINJA_CLIENT_ID = os.getenv("NINJA_CLIENT_ID")
NINJA_CLIENT_SECRET = os.getenv("NINJA_CLIENT_SECRET")
NINJA_TOKEN_URL = os.getenv("NINJA_TOKEN_URL")
NINJA_SCOPE = os.getenv("NINJA_SCOPE")
NINJA_API_BASE_URL = os.getenv("NINJA_API_BASE_URL")

ninja = NinjaRMMClient(
    client_id=NINJA_CLIENT_ID,
    client_secret=NINJA_CLIENT_SECRET,
    token_url=NINJA_TOKEN_URL,
    scope=NINJA_SCOPE
)

# Add allowed IPs to database
# ip_counts = retrieve_all_ips()

# # Add allowed IPs to database
# INITIAL_IPS = [
#     IPConfig(
#         ip_address=ip['publicIP'],
#         device_name='',  # Empty as not provided in ip_counts
#         client_name=ip['name_client'],
#         location_name=ip['name_location'],
#         is_static_ip=True,
#         push_url=''  # Empty to be filled later
#     )
#     for ip in ip_counts
# ]

# # Add initial IPs to database
# for ip_config in INITIAL_IPS:
#     db_manager.add_ip(ip_config)

TCP_PORT = 50000
API_PORT = 8008

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)

async def run_tcp_monitor():
    monitor = TCPMonitor(
        db_manager=db_manager,
        port=TCP_PORT
    )
    await monitor.start_server()

if __name__ == '__main__':
    # Start API server in a separate process
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()

    # Run TCP monitor in the main process
    asyncio.run(run_tcp_monitor()) 