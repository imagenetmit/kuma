import requests
import json
import os
import base64
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from pymongo import UpdateOne, MongoClient
from ninjapy.client import NinjaRMMClient
import asyncio
import aiohttp
#from tqdm.asyncio import tqdm_asyncio
import time
from dotenv import load_dotenv
from aiohttp import ClientSession, TCPConnector
from asyncio import Semaphore
from openai import OpenAI
import re
import ipaddress
load_dotenv(override=True)
# Define the base URL and endpoints
BASE_URL = "https://api-na.myconnectwise.net/v2025_1/apis/3.0"
COMPANY_ID = os.getenv('PROD_COMPANY_ID')
CLIENT_ID = os.getenv('PROD_CLIENT_ID')
PUBLIC_KEY = os.getenv('PROD_PUBLIC_KEY')
PRIVATE_KEY = os.getenv('PROD_PRIVATE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI')
#COMPANY_ID = os.getenv('SANDBOX_COMPANY_ID')
#CLIENT_ID = os.getenv('SANDBOX_CLIENT_ID')
#PUBLIC_KEY = os.getenv('SANDBOX_PUBLIC_KEY')
#PRIVATE_KEY = os.getenv('SANDBOX_PRIVATE_KEY')

SIMPLESAT_API_KEY = os.getenv('SIMPLESAT_API_KEY')
SIMPLESAT_API_BASE_URL = os.getenv('SIMPLESAT_API_BASE_URL')
ITGLUE_API_KEY = os.getenv('ITGLUE_API_KEY')
ITGLUE_API_BASE_URL = os.getenv('ITGLUE_API_BASE_URL')
# CWAUTOMATE_APITOKEN_REFRESH_ENDPOINT = os.getenv('CWAUTOMATE_APITOKEN_REFRESH_ENDPOINT')
# CWAUTOMATE_APITOKEN_ENDPOINT = os.getenv('CWAUTOMATE_APITOKEN_ENDPOINT')
# CWAUTOMATE_API_BASE_URL = os.getenv('CWAUTOMATE_API_BASE_URL')
# CWAUTOMATE_USERNAME = os.getenv('CWAUTOMATE_USERNAME')
# CWAUTOMATE_PASSWORD = os.getenv('CWAUTOMATE_PASSWORD')
CW_CLIENT_ID = os.getenv('CW_CLIENT_ID')

rate_limiter = None
semaphore = None


async def get_itglue_data(endpoint, params, headers):
    """
    Fetch data from ITGlue API with pagination support using concurrent requests.
    
    Args:
        endpoint (str): The ITGlue API endpoint URL
            'organizations' for 'https://api.itglue.com/organizations'
        params (dict): Query parameters for the API request
            'page[size]': 1000,
            'filter[organization_status_id]': 11966,
            'filter[exclude][organization_type_id]': "134304,134324,174540,134322,135821,135823"
        headers (dict): Headers for the API request
            'Accept': 'application/json',
            'x-api-key': ITGLUE_API_KEY,
            'Content-Type': 'application/vnd.api+json'
        
    Returns:
        list: All data items retrieved from the API
    """
    url = f"{ITGLUE_API_BASE_URL}/{endpoint}"
    all_data = []
    max_concurrent_requests = 5  # Adjust based on API limits
    retry_attempts = 3
    retry_delay = 1  # seconds
    
    async def fetch_page(session, page_number):
        page_params = params.copy()
        page_params["page[number]"] = page_number
        
        for attempt in range(retry_attempts):
            try:
                async with session.get(url, headers=headers, params=page_params) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return response_data
                    elif response.status == 429:  # Rate limit hit
                        retry_after = int(response.headers.get('Retry-After', retry_delay))
                        print(f"Rate limit hit, waiting {retry_after} seconds...")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        print(f"Failed to retrieve page {page_number}. Status code: {response.status}")
                        return None
            except Exception as e:
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                print(f"Error fetching page {page_number}: {str(e)}")
                return None
        return None

    # Get initial page to determine total pages
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=max_concurrent_requests)) as session:
        initial_data = await fetch_page(session, 1)
        if not initial_data:
            print("Failed to retrieve initial page")
            return []

        all_data.extend(initial_data['data'])
        meta = initial_data.get('meta', {})
        total_pages = meta.get('total-pages', 1)
        
        if total_pages > 1:
            print(f"Found {total_pages} total pages. Starting concurrent fetches...")
            
            # Create semaphore for rate limiting
            semaphore = asyncio.Semaphore(max_concurrent_requests)
            
            async def fetch_with_semaphore(page):
                async with semaphore:
                    return await fetch_page(session, page)
            
            # Fetch remaining pages concurrently
            tasks = [fetch_with_semaphore(page) for page in range(2, total_pages + 1)]
            results = await asyncio.gather(*tasks)
            
            # Process results
            for result in results:
                if result and 'data' in result:
                    all_data.extend(result['data'])
                    
        print(f"Total items retrieved: {len(all_data)}")
        
    return all_data

# Add validation utility functions at module level
def validate_ip(ip_str):
    """Validate an IP address using ipaddress library"""
    if not ip_str:
        return False
    try:
        ip = ipaddress.ip_address(ip_str)
        return isinstance(ip, ipaddress.IPv4Address)
    except ValueError:
        return False

def validate_subnet_mask(mask_str):
    """Validate a subnet mask using ipaddress library"""
    if not mask_str:
        return False
    try:
        # Convert to int to check if it's a valid netmask
        mask = ipaddress.IPv4Address(mask_str)
        mask_int = int(mask)
        # Check if it's a valid netmask pattern (continuous 1s followed by continuous 0s)
        mask_bin = bin(mask_int)[2:].zfill(32)
        return '01' not in mask_bin and mask_bin.count('1') > 0
    except ValueError:
        return False

def validate_cidr(cidr_str):
    """Validate a CIDR block using ipaddress library"""
    if not cidr_str:
        return False
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        return isinstance(network, ipaddress.IPv4Network)
    except ValueError:
        return False

def validate_ip_range(range_str):
    """Validate an IP range using ipaddress library"""
    if not range_str or '-' not in range_str:
        return False
    try:
        start, end = map(str.strip, range_str.split('-'))
        start_ip = ipaddress.ip_address(start)
        end_ip = ipaddress.ip_address(end)
        return (isinstance(start_ip, ipaddress.IPv4Address) and 
               isinstance(end_ip, ipaddress.IPv4Address) and 
               start_ip <= end_ip)
    except ValueError:
        return False

# Validation functions for checking against text
def validate_ip_in_text(ip, text):
    """Check if a valid IP address exists in the text"""
    if not ip or not isinstance(ip, str):
        return True  # Return True for null values
    try:
        # First validate it's a proper IP address
        ipaddress.ip_address(ip)
        # Then check if it appears in the text
        escaped_ip = ip.replace('.', r'\.')
        return bool(re.search(escaped_ip, text))
    except ValueError:
        return False

def validate_cidr_in_text(cidr, text):
    """Check if a valid CIDR block exists in the text"""
    if not cidr or not isinstance(cidr, str):
        return True  # Return True for null values
    try:
        # First validate it's a proper CIDR
        ipaddress.ip_network(cidr, strict=False)
        # Then check if it appears in the text
        escaped_cidr = cidr.replace('.', r'\.').replace('/', r'\/')
        return bool(re.search(escaped_cidr, text))
    except ValueError:
        return False

def validate_ip_range_in_text(ip_range, text):
    """Check if a valid IP range exists in the text"""
    if not ip_range or not isinstance(ip_range, str):
        return True
    try:
        start, end = ip_range.split('-')
        # Validate both IPs
        ipaddress.ip_address(start.strip())
        ipaddress.ip_address(end.strip())
        # Check if range appears in text
        escaped_range = ip_range.replace('.', r'\.').replace('-', r'\-')
        return bool(re.search(escaped_range, text))
    except (ValueError, AttributeError):
        return False


async def get_ninja_devices(ninja: NinjaRMMClient, use_cache=True):
    """Fetch Ninja RMM devices data from cache or API.
    
    This function manages the caching of device data from Ninja RMM to reduce API calls.
    It checks if cached data exists and is less than 1 hour old. If the cache is valid, it returns
    the cached data. Otherwise, it fetches fresh data from the Ninja RMM API and updates the cache.
    
    Args:
        ninja (NinjaRMMClient): Initialized Ninja RMM client
        use_cache (bool): Whether to use cached data if available
        
    Returns:
        list: List of dictionaries containing device data from Ninja RMM
            
    Cache behavior:
        - Cache file: 'ninja_devices.json'
        - Cache duration: 1 hour
        - Cache format: JSON file with indented formatting
    """
    devices_file = './ninja_devices.json'
    cache_max_age = 1 * 60 * 60  # 1 hour in seconds

    fetch_cache = use_cache  # Skip cache check if use_cache is False
    if fetch_cache and os.path.exists(devices_file):
        devices_age = time.time() - os.path.getmtime(devices_file)
        if devices_age < cache_max_age:
            print("Loading cached ninja devices data from JSON file")
            try:
                with open(devices_file, 'r', encoding='utf-8') as f:
                    devices = json.load(f)
                print(f"Successfully loaded {len(devices)} devices from cache")
                return devices
            except Exception as e:
                print(f"Error loading cached ninja devices data: {str(e)}")
                fetch_cache = False
        else:
            fetch_cache = False
            print("Cache is expired, fetching fresh devices data")
    else:
        fetch_cache = False
        print("Fetching ninja devices data from API")
        
    # Fetch fresh data
    devices = ninja.get_devices_detailed()
    print(f"Successfully fetched {len(devices)} records from Ninja API")
    
    # Cache the fresh data
    try:
        with open(devices_file, 'w') as f:
            json.dump(devices, f, indent=4, default=str)
    except Exception as e:
        print(f"Warning: Failed to cache devices data: {str(e)}")

    return devices

async def get_ninja_organizations(ninja: NinjaRMMClient, use_cache=True):
    """Fetch Ninja RMM organizations data from cache or API.
    
    This function manages the caching of organization data from Ninja RMM to reduce API calls.
    It checks if cached data exists and is less than 1 hour old. If the cache is valid, it returns
    the cached data. Otherwise, it fetches fresh data from the Ninja RMM API and updates the cache.
    
    Args:
        ninja (NinjaRMMClient): Initialized Ninja RMM client
        use_cache (bool): Whether to use cached data if available
        
    Returns:
        list: List of dictionaries containing organization data from Ninja RMM
            
    Cache behavior:
        - Cache file: 'ninja_organizations.json'
        - Cache duration: 1 hour
        - Cache format: JSON file with indented formatting
    """
    organizations_file = './ninja_organizations.json'
    cache_max_age = 1 * 60 * 60  # 1 hour in seconds

    fetch_cache = use_cache  # Skip cache check if use_cache is False
    if fetch_cache and os.path.exists(organizations_file):
        organizations_age = time.time() - os.path.getmtime(organizations_file)
        if organizations_age < cache_max_age:
            print("Loading cached ninja organizations data from JSON file")
            try:
                with open(organizations_file, 'r', encoding='utf-8') as f:
                    organizations = json.load(f)
                print(f"Successfully loaded {len(organizations)} organizations from cache")
                return organizations
            except Exception as e:
                print(f"Error loading cached ninja organizations data: {str(e)}")
                fetch_cache = False
        else:
            fetch_cache = False
            print("Cache is expired, fetching fresh organizations data")
    else:
        fetch_cache = False
        print("Fetching ninja organizations data from API")
        
    # Fetch fresh data
    organizations = ninja.get_organizations_detailed()
    print(f"Successfully fetched {len(organizations)} records from Ninja API")
    
    # Cache the fresh data
    try:
        with open(organizations_file, 'w') as f:
            json.dump(organizations, f, indent=4, default=str)
    except Exception as e:
        print(f"Warning: Failed to cache organizations data: {str(e)}")

    return organizations

def initialize_rate_limiter(requests_per_second=20, max_concurrent=10):
    global rate_limiter, semaphore
    rate_limiter = RateLimiter(requests_per_second)
    semaphore = Semaphore(max_concurrent)

class RateLimiter:
    def __init__(self, rate):
        self.rate = rate
        self.tokens = rate
        self.last_update = time.monotonic()

    async def acquire(self):
        while True:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.tokens += time_passed * self.rate
            if self.tokens > self.rate:
                self.tokens = self.rate
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                await asyncio.sleep(1 / self.rate)


async def get_agreement_additions():
    global rate_limiter, semaphore
    if rate_limiter is None or semaphore is None:
        initialize_rate_limiter()

    agreement_recap_endpoint = f'{BASE_URL}/finance/agreementrecaps'
    agreement_additions_endpoint = f'{BASE_URL}/finance/agreements'

    recap_fields = ["id", "name", "agreementId", "agreementStatus"]
    recap_params = {
        'fields': ",".join(recap_fields),
        'pageSize': 1000,
        'conditions': 'agreementStatus="Active"'
    }

    additions_fields = ["id", "quantity","unitPrice","unitCost","billCustomer","billedQuantity","extPrice","extCost","effectiveDate","description", "billCustomer", "effectiveDate", "cancelledDate", "billableAmount","product/identifier","cancelledDate"]
    additions_params = {
        'fields': ",".join(additions_fields),
        'pageSize': 1000
    }

    async with semaphore:
        await rate_limiter.acquire()
        try:
            connector = TCPConnector(limit=None, ttl_dns_cache=300)
            async with ClientSession(connector=connector) as session:
                active_recaps = await fetch_all_pages(session, agreement_recap_endpoint, recap_params)

                results = []
                for recap in active_recaps:
                    await rate_limiter.acquire()
                    additions_endpoint = f"{agreement_additions_endpoint}/{recap['agreementId']}/additions"
                    additions = await fetch_all_pages(session, additions_endpoint, additions_params)
                    results.append({
                        'recap': recap,
                        'additions': additions
                    })

            return results
        except Exception as e:
            print(f"Error fetching active agreement recaps with additions: {str(e)}")
            return []

async def fetch_all_pages(session, endpoint, params):
    all_data = []
    page = 1

    while True:
        params['page'] = page
        async with session.get(endpoint, params=params) as response:
            if response.status != 200:
                raise Exception(f"API request failed with status {response.status}: {await response.text()}")
            
            data = await response.json()
            all_data.extend(data)

            if len(data) < params['pageSize']:
                break

            page += 1

    return all_data


async def get_all_ticket_notes(ticket_id):
    global rate_limiter, semaphore
    if rate_limiter is None or semaphore is None:
        initialize_rate_limiter()

    notes_endpoint = f'{BASE_URL}/service/tickets/{ticket_id}/allnotes'
    time_endpoint = f'{BASE_URL}/time/entries'

    time_fields = ["id","company/name","member/name","internalNotes","enteredBy","dateEntered"]
    time_params = {
        'fields': ",".join(time_fields),
        'pageSize': 1000,
        'conditions': f"ticket/id={ticket_id}"
    }

    note_fields = ["id","noteType","ticket/id","text","member/name","internalAnalysisFlag","contact/name","customerUpdatedFlag","_info/dateEntered","_info/enteredBy"]
    note_params = {
        'fields': ",".join(note_fields),
        'pageSize': 250
    }
    if ticket_id % 5 == 0:
        print(f"Getting notes for ticket {ticket_id}")
    
    count_params = {
    }

    async with semaphore:
        await rate_limiter.acquire()
        try:
            # First check the notes count to determine how to proceed
            notes_count_endpoint = f'{BASE_URL}/service/tickets/{ticket_id}/notes/count'
            notes_single_page_endpoint = f'{BASE_URL}/service/tickets/{ticket_id}/notes'
            
            connector = TCPConnector(limit=None, ttl_dns_cache=300)
            async with ClientSession(connector=connector) as session:
                try:
                    # Get the notes count and first page in parallel
                    count_task = asyncio.create_task(fetch_page(notes_count_endpoint, count_params, 1))
                    first_page_task = asyncio.create_task(fetch_page(notes_single_page_endpoint, note_params, 1))
                    
                    notes_count, notes_page1 = await asyncio.gather(count_task, first_page_task)
                    
                    print(f"Got {notes_count[0].get('count', 0)} notes for ticket {ticket_id}")
                    
                    # Check if notes count is greater than 250
                    if notes_count[0].get('count', 0) > 250:
                        # Check if the first note in notes_page1 contains the specified text
                        if isinstance(notes_page1, list) and notes_page1 and isinstance(notes_page1[0], dict):
                            if notes_page1 and len(notes_page1) > 0 and 'text' in notes_page1[0]:
                                note_text = notes_page1[0].get('text', '')
                                if "type: SaaS Alerts Respond - Rule Triggered" in note_text:
                                    # Prepend a warning message to the first note's text  
                                    # notes_page1[0]['text'] = "SAAS ALERT NOTES TRUNCATED DUE TO LENGTH " + notes_page1[0]['text']
                                    print(f"SaaS Alerts ticket: Returning only page1 notes for ticket {ticket_id} due to high count.")
                                    notes_task = asyncio.create_task(fetch_page(notes_single_page_endpoint, note_params, 1))
                                    time_task = asyncio.create_task(fetch_all_pages(session, time_endpoint, time_params))
                                    notes, time_entries = await asyncio.gather(notes_task, time_task)
                                else:
                                    # notes_page1[0]['text'] = "NOTES COUNT >250: NOTES TRUNCATED DUE TO LENGTH " + notes_page1[0]['text']
                                    print(f"High notes count: Returning only page1 notes for ticket {ticket_id} due to high count.")
                                    notes_task = asyncio.create_task(fetch_page(notes_single_page_endpoint, note_params, 1))    
                                    time_task = asyncio.create_task(fetch_all_pages(session, time_endpoint, time_params))
                                    notes, time_entries = await asyncio.gather(notes_task, time_task)
                    else:
                        # If we didn't return early, continue with full fetching
                        notes_task = asyncio.create_task(fetch_all_pages(session, notes_endpoint, note_params))
                        time_task = asyncio.create_task(fetch_all_pages(session, time_endpoint, time_params))
                        notes, time_entries = await asyncio.gather(notes_task, time_task)
                except Exception as e:
                    print(f"Error during preliminary checks for ticket {ticket_id}: {str(e)}")
                    return []

            # Create a dictionary to store time entries by their ID
            time_dict = {entry['id']: entry for entry in time_entries}

            # Process notes and append internal notes from time entries
            for note in notes:
                if note['id'] in time_dict:
                    time_entry = time_dict[note['id']]
                    if time_entry.get('internalNotes'):
                        if 'text' not in note:
                            note['text'] = f"***Internal Note***\n{time_entry['internalNotes']}"
                        else:
                            note['text'] += f"\n***Internal Note***\n{time_entry['internalNotes']}"
            
            return notes
        except Exception as e:
            print(f"Error fetching notes for ticket {ticket_id}: {str(e)}")
            return []
        
async def fetch_page(endpoint, params, page):
    params['page'] = page
    print(f"Fetching page {page} with conditions: {params}")
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, params=params, headers=get_headers()) as response:
            if response.status == 200:
                page_data = await response.json()
                print(f"Received {len(page_data)} tickets on page {page}")
                return page_data, response.headers
            else:
                print(f"Error: {response.status} - {await response.text()}")
                return [], {}
async def fetch_all_pages(session, endpoint, params):
    all_data = []
    page = 1
    max_retries = 10
    retry_delay = 1

    while True:
        for attempt in range(max_retries):
            try:
                page_data, headers = await fetch_page_data(session, endpoint, params, page)
                if not page_data:
                    return all_data
                all_data.extend(page_data)
                page += 1
                if 'next' not in headers.get('Link', ''):
                    return all_data
                break  # Successful, break the retry loop
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to fetch page {page} after {max_retries} attempts: {str(e)}")
                    return all_data
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
async def fetch_page_data(session, endpoint, params, page):
    params['page'] = page
    HEADERS = get_headers()
    async with session.get(endpoint, params=params, headers=HEADERS) as response:
        if response.status == 200:
            data = await response.json()
            return data, response.headers
        else:
            raise Exception(f"Error: {response.status} - {await response.text()}")

async def get_single_ticket_async(ticket_id, fields=[],conditions=None,allFields=False):
    if allFields:
        default_ticket_fields = []
    else:
        default_ticket_fields = [
            "id", "summary", "board/name", "board/id", "status/name", "company/name", "contact/name", "type/name", "subType/name", "item/name", "owner/name", "priority/name", "source/id", "source/name", "dateEntered",
            "closedDate", "closedBy", "actualHours", "resources", "respondedBy", "resolvedBy", "parentTicketId"
        ]
    ticket_fields_str = ",".join(fields) if fields else ",".join(default_ticket_fields)
    
    tickets_endpoint = f'{BASE_URL}/service/tickets/{ticket_id}'
    params = {
        'fields': ticket_fields_str,
        'conditions': conditions if conditions else ''
    }
    if ticket_id % 5 == 0:
        print(f"Getting ticket {ticket_id}")

    async with aiohttp.ClientSession() as session:
        async with session.get(tickets_endpoint, params=params, headers=get_headers()) as response:
            if response.status == 200:
                ticket = await response.json()
                return ticket, response.headers
            else:
                print(f"Error: {response.status} - {await response.text()}")
                return None, {}
async def get_multiple_tickets_async(fields=[], allFields=False,conditions=None, orderBy=None, limit=100):
    if allFields:
        default_ticket_fields = []
    else:
        default_ticket_fields = [
            "id", "summary", "board/name", "board/id", "status/name", "company/name", "contact/name", "type/name", "subType/name", "item/name", "owner/name", "priority/name", "source/id", "source/name", "dateEntered",
            "closedDate", "closedBy", "actualHours", "resources", "respondedBy", "resolvedBy", "parentTicketId"
        ]
    ticket_fields_str = ",".join(fields) if fields else ",".join(default_ticket_fields)
    
    tickets_endpoint = f'{BASE_URL}/service/tickets'
  
    params = {
        'fields': ticket_fields_str,
        'pageSize': 1000 if limit > 1000 else limit,
        'orderBy': orderBy or 'id desc',
        'conditions': conditions if conditions else ''
    }
    
    async def fetch_page(session, page):
        page_params = {**params, 'page': page}
        async with session.get(tickets_endpoint, params=page_params, headers=get_headers()) as response:
            if response.status == 200:
                return await response.json(), response.headers
            else:
                print(f"Error: {response.status} - {await response.text()}")
                return [], {}

    tickets = []
    async with aiohttp.ClientSession() as session:
        page = 1
        while True:
            page_tickets, headers = await fetch_page(session, page)
            tickets.extend(page_tickets)
            if len(tickets) >= limit or 'next' not in headers.get('Link', ''):
                break
            page += 1

    # print(f"Fetch complete. Total tickets: {len(tickets)}")
    return tickets[:limit]
# Wrapper function to run the async function
def get_all_ticket_notes_sync(ticket_id):
    return asyncio.run(get_all_ticket_notes(ticket_id))
def get_encoded_auth():
    auth_string = f"{COMPANY_ID}+{PUBLIC_KEY}:{PRIVATE_KEY}"
    return base64.b64encode(auth_string.encode()).decode()
def get_headers():
    auth_string = f"{COMPANY_ID}+{PUBLIC_KEY}:{PRIVATE_KEY}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    return {
        'clientId': CLIENT_ID,
        'Authorization': f'Basic {encoded_auth}',
        'Content-Type': 'application/json'
    }

rate_limiter = None
semaphore = None

def initialize_rate_limiter(requests_per_second=5, max_concurrent=5):
    global rate_limiter, semaphore
    rate_limiter = RateLimiter(requests_per_second)
    semaphore = Semaphore(max_concurrent)

def get_mongodb_client():

    if not MONGODB_URI:
        print("Error: MONGODB_URI environment variable is not set")
        raise ValueError("MONGODB_URI environment variable is required")
    print(f"Connecting to MongoDB at: {MONGODB_URI}")
    client = MongoClient(host=MONGODB_URI)
    print("Connected to MongoDB...")
    return client
def upsert_documents(db_name, collection_name, documents,id_field='Id'):
    mongo_client = get_mongodb_client()
    db = mongo_client[db_name]
    collection = db[collection_name]

    update_operations = [
        UpdateOne({'id': document[id_field]}, {'$set': document}, upsert=True)
        for document in documents
    ]

    result = collection.bulk_write(update_operations)
    print(f"Matched {result.matched_count} document(s)")
    print(f"Modified {result.modified_count} document(s)")
    print(f"Upserted {result.upserted_count} document(s)")

    # Update the process_log
    most_recent_doc = max(documents, key=lambda x: x.get('updated-at', datetime.now(timezone.utc)))
    most_recent_update = most_recent_doc.get('updated-at', datetime.now(timezone.utc))
    process_log = db['process_log']
    process_log.insert_one({
        'timestamp': datetime.now(timezone.utc),
        'last_updated': most_recent_update,
        'documents_processed': len(documents),
        'collections_modified': [collection_name],
        'document_ids': [document['id'] for document in documents] if documents else []
    })

def replace_all_documents(db_name, collection_name, documents, id_field='Id'):
    """
    Replaces all documents in the specified collection with the new documents.
    
    Args:
        db_name (str): The name of the database
        collection_name (str): The name of the collection
        documents (list): List of documents to insert
        id_field (str): The field to use as the document identifier
        
    Returns:
        dict: Result of the operation
    """
    mongo_client = get_mongodb_client()
    db = mongo_client[db_name]
    collection = db[collection_name]
    
    # Drop the existing collection
    collection.drop()
    
    # Insert the new documents
    if documents:
        result = collection.insert_many(documents)
        inserted_count = len(result.inserted_ids)
    else:
        inserted_count = 0
    
    print(f"Replaced collection with {inserted_count} new document(s)")
    
    # Update the process_log
    if documents:
        most_recent_ticket = max(documents, key=lambda x: x.get('updated-at', '1970-01-01T00:00:00Z'))
        most_recent_update = most_recent_ticket.get('updated-at', '1970-01-01T00:00:00Z')
    else:
        most_recent_update = datetime.now(timezone.utc).isoformat()
        
    process_log = db['process_log']
    process_log.insert_one({
        'timestamp': datetime.now(timezone.utc),
        'last_updated': most_recent_update,
        'documents_processed': len(documents),
        'collections_modified': [collection_name],
        'operation': 'replace_all',
        'document_ids': [document.get(id_field) for document in documents] if documents else []
    })
    
    mongo_client.close()
    return {
        'inserted_count': inserted_count,
        'collection': collection_name
    }


def retrieve_documents(db_name, collection_name, filter_query=None, projection=None):
    mongo_client = get_mongodb_client()
    db = mongo_client[db_name]
    collection = db[collection_name]

    cursor = collection.find(filter_query or {}, projection)
    documents = list(cursor)
    print(f"Retrieved {len(documents)} document(s)")
    mongo_client.close()
    return documents


def get_simplesat_data(ticket_ids=[], start_date=None, end_date=None):
    survey_token = "EheLwpkfBS-PwZolwAt95u6UileEge0uGirXTI0GWO4"
    
    url = f"{SIMPLESAT_API_BASE_URL}/responses/search"
    filters = [{
        "key": "ticket_id",
        "values": ticket_ids,
        "comparison": "is"
    }] if ticket_ids else []
    
    data = {        
        "start_date": start_date if start_date else None,
        "survey": survey_token,
        "page_size": 100,
        "filters": filters if filters else []
    }
    
    headers = {
        'X-Simplesat-Token': SIMPLESAT_API_KEY,
        'Content-Type': 'application/json'
    }

    all_responses = []


    while True:
        
        payload = json.dumps(data)
        #print(payload)
        response = requests.post(url, headers=headers, data=payload)
        response_data = response.json()

        if 'responses' in response_data:
            print(response_data)
            all_responses.append(response_data)

        if response_data.get('next') is not None:
            url = response_data['next']
        else:
            break

    key = all_responses[0]
    data = key['responses']

    return data
def get_data_from_api(endpoint, params, page=1):
    # Base64 encode the company ID, public key, and private key for authentication
    auth_string = f"{COMPANY_ID}+{PUBLIC_KEY}:{PRIVATE_KEY}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    HEADERS = {
    'clientId': CLIENT_ID,
    'Authorization': f'Basic {encoded_auth}',
    'Content-Type': 'application/json'
    }
    params['page'] = page
    response = requests.get(endpoint, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json(), response.headers
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return [], {}   

def get_single_ticket(ticket_id, fields=[]):
    default_ticket_fields = [
        "id", "summary", "board/name", "board/id", "status/name", "company/name", "contact/name", "type/name", "subType/name", "item/name", "owner/name", "priority/name", "source/id", "source/name", "dateEntered",
        "closedDate", "closedBy", "actualHours", "resources", "respondedBy", "resolvedBy", "parentTicketId"
    ]
    ticket_fields_str = ",".join(fields) if fields else ",".join(default_ticket_fields)
    
    tickets_endpoint = f'{BASE_URL}/service/tickets/{ticket_id}'
    params = {
        'fields': ticket_fields_str
    }
    
    ticket, headers = get_data_from_api(tickets_endpoint, params)
    return ticket, headers
def to_datetime(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


async def post_data_async(endpoint, data, api_key, additional_headers=None):
    """
    Asynchronously post data to an endpoint with API key authentication
    
    Args:
        endpoint (str): The full URL endpoint to post to
        data (dict): The data to send in the request body
        api_key (str): The API key for authentication
        additional_headers (dict, optional): Any additional headers to include
        
    Returns:
        tuple: (success (bool), response_data (dict), status_code (int))
    """
    # Base headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain'  # Accept both JSON and plain text responses
    }
    
    # Add any additional headers
    if additional_headers:
        headers.update(additional_headers)
    
    # Add API key as query parameter
    params = {'key': api_key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, 
                                  headers=headers, 
                                  params=params,
                                  json=data,
                                  ssl=True) as response:
                
                content_type = response.headers.get('Content-Type', '')
                status_code = response.status
                
                # Handle different response types
                if 'application/json' in content_type:
                    response_data = await response.json()
                else:
                    response_data = await response.text()  # Get plain text response
                
                if status_code in range(200, 300):
                    return True, response_data, status_code
                else:
                    print(f"Error posting to {endpoint}: Status {status_code}")
                    print(f"Response: {response_data}")
                    return False, response_data, status_code
                    
    except aiohttp.ClientError as e:
        print(f"Network error occurred: {str(e)}")
        return False, {"error": str(e)}, 0
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {str(e)}")
        return False, {"error": "Invalid JSON response"}, 0
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False, {"error": str(e)}, 0


