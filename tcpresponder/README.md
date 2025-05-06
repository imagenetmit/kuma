# TCP Responder Service

A service that monitors TCP connections and syncs with Uptime Kuma's heartbeat data.

## Prerequisites

- Python 3.8+
- MariaDB 10.5+
- Redis

## MariaDB Configuration

For the binlog sync service to work, your MariaDB server must have binary logging enabled. Add these settings to your MariaDB configuration:

```ini
[mysqld]
server-id = 1
log-bin = mysql-bin
binlog_format = ROW
binlog_row_image = FULL
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```
   UPTIME_KUMA_DB_TYPE=mariadb
   UPTIME_KUMA_DB_HOSTNAME=your_host
   UPTIME_KUMA_DB_PORT=3306
   UPTIME_KUMA_DB_NAME=your_database
   UPTIME_KUMA_DB_USERNAME=your_username
   UPTIME_KUMA_DB_PASSWORD=your_password
   REDIS_HOST=redis
   REDIS_PORT=6379
   ```

## Running the Service

The service consists of multiple components:

1. API Server:
   ```bash
   python main.py
   ```

2. Sync Service (for binlog replication):
   ```bash
   python sync_service.py
   ```

## Dependencies

- `fastapi==0.109.2` - API framework
- `uvicorn==0.27.1` - ASGI server
- `aiohttp==3.9.3` - Async HTTP client
- `pydantic==2.6.1` - Data validation
- `requests==2.31.0` - HTTP client
- `pandas==2.2.0` - Data manipulation
- `python-dotenv==1.0.1` - Environment variables
- `mariadb==1.1.9` - MariaDB connector
- `redis==5.0.1` - Redis client
- `sqlalchemy==2.0.27` - Database ORM
- `pymysqlreplication==0.30` - Binlog replication

## Docker Support

The service can be run using Docker Compose:

```bash
docker compose up -d
```

## Logging

Logs are written to:
- `tcp_connections.log` - TCP connection events
- `sync_service.log` - Binlog sync events 