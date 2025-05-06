#!/bin/bash

# Database optimization script for Uptime Kuma
# This script helps improve dashboard performance by:
# 1. Adding missing indexes to large tables
# 2. Cleaning up old data
# 3. Optimizing database tables

echo "Starting Uptime Kuma database optimization..."

# Check if containers are running
if ! docker ps | grep -q kuma; then
  echo "Error: Uptime Kuma containers are not running."
  exit 1
fi

# Add missing indexes and optimize database
echo "Adding missing indexes and optimizing database..."
docker exec kuma node -e "
const mysql = require('mysql2/promise');
async function optimize() {
  try {
    const conn = await mysql.createConnection({
      host: 'mariadb',
      user: 'kuma',
      password: 'a7Bx9cD2eF4gH6jK8mN0pQ1rS3tU5vW7y',
      database: 'kuma'
    });
    
    // Check if timestamp index exists on heartbeat table
    const [heartbeatIndexes] = await conn.execute(\"SHOW INDEX FROM heartbeat WHERE Key_name = 'heartbeat_time_index'\");
    if (heartbeatIndexes.length === 0) {
      console.log('Adding time index to heartbeat table...');
      await conn.execute('CREATE INDEX heartbeat_time_index ON heartbeat(time)');
      console.log('Index added.');
    } else {
      console.log('Heartbeat time index already exists.');
    }
    
    // Check if timestamp index exists on stat_minutely table
    const [statIndexes] = await conn.execute(\"SHOW INDEX FROM stat_minutely WHERE Key_name = 'stat_minutely_timestamp_index'\");
    if (statIndexes.length === 0) {
      console.log('Adding timestamp index to stat_minutely table...');
      await conn.execute('CREATE INDEX stat_minutely_timestamp_index ON stat_minutely(timestamp)');
      console.log('Index added.');
    } else {
      console.log('Stat_minutely timestamp index already exists.');
    }
    
    // Clean up old data (older than 30 days)
    console.log('Cleaning up old heartbeat data...');
    const [heartbeatResult] = await conn.execute('DELETE FROM heartbeat WHERE time < DATE_SUB(NOW(), INTERVAL 30 DAY)');
    console.log('Deleted ' + heartbeatResult.affectedRows + ' old heartbeat records.');
    
    console.log('Cleaning up old stat_minutely data...');
    const [statResult] = await conn.execute('DELETE FROM stat_minutely WHERE timestamp < UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))');
    console.log('Deleted ' + statResult.affectedRows + ' old stat_minutely records.');
    
    // Optimize tables
    console.log('Optimizing tables...');
    await conn.execute('OPTIMIZE TABLE heartbeat, stat_minutely, stat_hourly, stat_daily, monitor, monitor_tag');
    console.log('Tables optimized.');
    
    await conn.end();
  } catch (error) {
    console.error('Error during optimization:', error);
    process.exit(1);
  }
}
optimize();
"

echo "Database optimization completed."

# Restart the containers to apply changes
read -p "Do you want to restart the Uptime Kuma containers to apply changes? (y/n): " RESTART
if [ "$RESTART" = "y" ] || [ "$RESTART" = "Y" ]; then
  echo "Restarting containers..."
  docker compose down
  docker compose up -d
  echo "Containers restarted."
fi

echo "Optimization completed. The dashboard should now load faster." 