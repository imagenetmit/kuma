import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import List, Set
from db_manager import DatabaseManager
from ninjapy.client import NinjaRMMClient
import os
from dotenv import load_dotenv

load_dotenv()

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
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tcp_connections.log'),
        logging.StreamHandler()
    ]
)

class TCPMonitor:
    def __init__(self, db_manager: DatabaseManager, port: int = 50000):
        self.db_manager = db_manager
        self.port = port

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer_name = writer.get_extra_info('peername')
        client_ip = peer_name[0] if peer_name else 'Unknown'
        # if not self.db_manager.is_ip_allowed(client_ip):
        #     logging.warning(f"Rejected connection from unauthorized IP: {client_ip}")
        #     writer.close()
        #     await writer.wait_closed()
        #     return

        # device = ninja.search_devices(query=client_ip, expand="organization,location")
        
        

        # logging.info(f"Accepted connection from: {client_ip}")
        
        # # Send webhook notification
        # await self.send_webhook(client_ip)
        try:
            device = ninja.search_devices(query=client_ip, expand="organization,location")
            
            logging.info(f"Accepted connection from: {client_ip}")
            
            # Send webhook notification
            await self.send_webhook(client_ip)
            
        except Exception as e:
            logging.error(f"Unhandled exception in handle_connection: {str(e)}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logging.error(f"Error closing connection: {str(e)}")

    async def send_webhook(self, client_ip: str):
        webhook_url = self.db_manager.get_webhook_url(client_ip)
        if not webhook_url:
            logging.error(f"No webhook URL found for IP: {client_ip}")
            return
            
        webhook_url = webhook_url.replace('msg=OK', f'msg=Connection_from_{client_ip}')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(webhook_url) as response:
                    if response.status != 200:
                        logging.error(f"Webhook failed with status {response.status}")
                    else:
                        logging.info("Webhook sent successfully")
        except Exception as e:
            logging.error(f"Error sending webhook: {str(e)}")

    async def start_server(self):
        server = await asyncio.start_server(
            self.handle_connection,
            '0.0.0.0',
            self.port
        )
        
        logging.info(f"Server started on port {self.port}")
        
        async with server:
            await server.serve_forever() 

    async def client_connected_cb(self, reader, writer):
        try:
            addr = writer.get_extra_info('peername')
            print(f"Client connected: {addr}")
            
            # Read data from the client
            data = await reader.read(100)
            message = data.decode()
            
            # Don't reuse coroutines - create a new one each time
            response = await self.generate_response(message)  # This is correct
            
            # Write response back to the client
            writer.write(response.encode())
            await writer.drain()
            
            # Close the connection
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            logging.error(f"Unhandled exception in client_connected_cb: {e}")
            import traceback
            logging.error(traceback.format_exc())

    # INCORRECT PATTERN (example of what might be causing the error):
    # async def some_function():
    #     coro = some_async_function()
    #     await coro  # First await - this is fine
    #     await coro  # Second await - this will cause the error

    # CORRECT PATTERN:
    # async def some_function():
    #     # Call the function twice to create two separate coroutines
    #     await some_async_function()  # First coroutine
    #     await some_async_function()  # Second coroutine - this is fine
