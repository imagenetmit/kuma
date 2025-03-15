#!/bin/bash

# Cleanup script for Uptime Kuma
# This script helps maintain the Uptime Kuma installation by:
# 1. Cleaning up orphaned database records
# 2. Truncating the error log
# 3. Optimizing database tables
# 4. Restarting the containers if needed

echo "Starting Uptime Kuma maintenance..."

# Check if containers are running
if ! docker ps | grep -q kuma; then
  echo "Error: Uptime Kuma containers are not running."
  exit 1
fi

# Truncate the error log if it's larger than 10MB
ERROR_LOG_SIZE=$(du -m data/error.log 2>/dev/null | cut -f1)
if [ -n "$ERROR_LOG_SIZE" ] && [ "$ERROR_LOG_SIZE" -gt 10 ]; then
  echo "Error log is ${ERROR_LOG_SIZE}MB, truncating..."
  truncate -s 0 data/error.log
  echo "Error log truncated."
fi

# Clean up orphaned database records
echo "Cleaning up orphaned database records..."
docker exec kuma node -e "
const mysql = require('mysql2/promise');
async function cleanup() {
  try {
    const conn = await mysql.createConnection({
      host: 'mariadb',
      user: 'kuma',
      password: 'a7Bx9cD2eF4gH6jK8mN0pQ1rS3tU5vW7y',
      database: 'kuma'
    });
    
    // Delete orphaned stat records
    const [result1] = await conn.execute('DELETE FROM stat_minutely WHERE monitor_id NOT IN (SELECT id FROM monitor)');
    console.log('Cleaned up ' + result1.affectedRows + ' orphaned stat_minutely records');
    
    // Delete old heartbeat records (older than 7 days)
    const [result2] = await conn.execute('DELETE FROM heartbeat WHERE time < DATE_SUB(NOW(), INTERVAL 7 DAY)');
    console.log('Cleaned up ' + result2.affectedRows + ' old heartbeat records');
    
    // Delete old stat_minutely records (older than 30 days)
    const [result3] = await conn.execute('DELETE FROM stat_minutely WHERE timestamp < UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))');
    console.log('Cleaned up ' + result3.affectedRows + ' old stat_minutely records');
    
    // Optimize tables
    await conn.execute('OPTIMIZE TABLE heartbeat, stat_minutely, stat_hourly, stat_daily, monitor, monitor_tag');
    console.log('Database tables optimized');
    
    await conn.end();
  } catch (error) {
    console.error('Error during cleanup:', error);
    process.exit(1);
  }
}
cleanup();
"

echo "Database cleanup completed."

# Check memory usage
MEMORY_USAGE=$(docker stats kuma --no-stream --format "{{.MemUsage}}" | awk '{print $1}')
echo "Current memory usage: $MEMORY_USAGE"

# Ask if user wants to restart containers
read -p "Do you want to restart the Uptime Kuma containers? (y/n): " RESTART
if [ "$RESTART" = "y" ] || [ "$RESTART" = "Y" ]; then
  echo "Restarting containers..."
  docker compose down
  docker compose up -d
  echo "Containers restarted."
fi

echo "Maintenance completed." 