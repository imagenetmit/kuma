#!/bin/bash

# Setup cron job for Uptime Kuma maintenance
# This script sets up a cron job to run the cleanup-kuma.sh script weekly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup-kuma.sh"

if [ ! -f "$CLEANUP_SCRIPT" ]; then
  echo "Error: cleanup-kuma.sh script not found at $CLEANUP_SCRIPT"
  exit 1
fi

# Create a temporary crontab file
TEMP_CRONTAB=$(mktemp)

# Export current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab" > "$TEMP_CRONTAB"

# Check if the cron job already exists
if grep -q "cleanup-kuma.sh" "$TEMP_CRONTAB"; then
  echo "Cron job for Uptime Kuma maintenance already exists."
else
  # Add the cron job to run weekly at 2 AM on Sunday
  echo "# Run Uptime Kuma maintenance weekly at 2 AM on Sunday" >> "$TEMP_CRONTAB"
  echo "0 2 * * 0 $CLEANUP_SCRIPT > $SCRIPT_DIR/cleanup-kuma.log 2>&1" >> "$TEMP_CRONTAB"
  
  # Install the new crontab
  crontab "$TEMP_CRONTAB"
  echo "Cron job for Uptime Kuma maintenance has been set up to run weekly."
fi

# Clean up
rm "$TEMP_CRONTAB"

echo "You can manually run the cleanup script at any time with:"
echo "$CLEANUP_SCRIPT" 