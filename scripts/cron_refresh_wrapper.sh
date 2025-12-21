#!/bin/bash
# Cron wrapper for materialized view refresh
# This script loads environment variables and calls the refresh script

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Set log file with timestamp
LOG_FILE="$PROJECT_DIR/logs/cron_refresh_$(date +%Y%m%d_%H%M%S).log"

# Run refresh script and log output
echo "==================================================" >> "$LOG_FILE"
echo "Automated Refresh Started: $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

cd "$PROJECT_DIR"
"$PROJECT_DIR/scripts/refresh_materialized_views.sh" >> "$LOG_FILE" 2>&1

echo "" >> "$LOG_FILE"
echo "Completed: $(date)" >> "$LOG_FILE"
echo "==================================================" >> "$LOG_FILE"

# Keep only last 30 days of logs
find "$PROJECT_DIR/logs" -name "cron_refresh_*.log" -mtime +30 -delete
