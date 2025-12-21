#!/bin/bash
# Setup Automated Materialized View Refresh
# This script sets up a cron job to automatically refresh materialized views

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Materialized View Automation Setup${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Get the absolute path to the project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
REFRESH_SCRIPT="$PROJECT_DIR/scripts/refresh_materialized_views.sh"
LOG_DIR="$PROJECT_DIR/logs"

echo -e "Project directory: ${YELLOW}$PROJECT_DIR${NC}"
echo -e "Refresh script: ${YELLOW}$REFRESH_SCRIPT${NC}"
echo -e "Log directory: ${YELLOW}$LOG_DIR${NC}"
echo ""

# Verify refresh script exists and is executable
if [ ! -f "$REFRESH_SCRIPT" ]; then
    echo -e "${RED}Error: Refresh script not found at $REFRESH_SCRIPT${NC}"
    exit 1
fi

# Make script executable
chmod +x "$REFRESH_SCRIPT"
echo -e "${GREEN}✓${NC} Refresh script is executable"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"
echo -e "${GREEN}✓${NC} Log directory created/verified"

# Create a wrapper script for cron (handles environment)
CRON_WRAPPER="$PROJECT_DIR/scripts/cron_refresh_wrapper.sh"
cat > "$CRON_WRAPPER" << 'EOF'
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
EOF

chmod +x "$CRON_WRAPPER"
echo -e "${GREEN}✓${NC} Cron wrapper script created"

# Display cron job options
echo ""
echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}Cron Job Configuration Options${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""
echo "Choose when to refresh materialized views:"
echo ""
echo "1) Daily at 2:00 AM (recommended for production)"
echo "2) Every 6 hours (for frequently updated data)"
echo "3) Daily at 3:00 AM (alternative time)"
echo "4) Manual setup (show cron command)"
echo "5) Skip cron setup (I'll configure it manually)"
echo ""
read -p "Enter choice [1-5]: " choice

CRON_SCHEDULE=""
case $choice in
    1)
        CRON_SCHEDULE="0 2 * * *"
        DESCRIPTION="Daily at 2:00 AM"
        ;;
    2)
        CRON_SCHEDULE="0 */6 * * *"
        DESCRIPTION="Every 6 hours"
        ;;
    3)
        CRON_SCHEDULE="0 3 * * *"
        DESCRIPTION="Daily at 3:00 AM"
        ;;
    4)
        echo ""
        echo -e "${GREEN}Manual cron setup command:${NC}"
        echo ""
        echo "crontab -e"
        echo ""
        echo "Then add this line:"
        echo ""
        echo -e "${YELLOW}0 2 * * * $CRON_WRAPPER${NC}"
        echo ""
        echo "(This runs daily at 2:00 AM)"
        exit 0
        ;;
    5)
        echo ""
        echo -e "${YELLOW}Skipping cron setup. To configure manually later, use:${NC}"
        echo ""
        echo "  bash $PROJECT_DIR/scripts/setup_automation.sh"
        echo ""
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Add cron job
echo ""
echo -e "${YELLOW}Adding cron job: $DESCRIPTION${NC}"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$CRON_WRAPPER"; then
    echo -e "${YELLOW}⚠ Cron job already exists. Removing old entry...${NC}"
    crontab -l 2>/dev/null | grep -v "$CRON_WRAPPER" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_WRAPPER") | crontab -

echo -e "${GREEN}✓${NC} Cron job added successfully!"
echo ""

# Display current crontab
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Current Cron Jobs:${NC}"
echo -e "${GREEN}=========================================${NC}"
crontab -l
echo ""

# Test the refresh script manually
echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}Testing Refresh Script${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""
read -p "Would you like to test the refresh script now? [y/N]: " test_choice

if [[ "$test_choice" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running refresh script..."
    "$CRON_WRAPPER"
    echo ""
    echo -e "${GREEN}✓${NC} Test complete! Check logs at: $LOG_DIR"
else
    echo ""
    echo "Skipping test. You can manually run:"
    echo "  $CRON_WRAPPER"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "Materialized views will be refreshed ${GREEN}$DESCRIPTION${NC}"
echo ""
echo "Useful commands:"
echo "  • View logs:           tail -f $LOG_DIR/cron_refresh_*.log"
echo "  • Manual refresh:      $REFRESH_SCRIPT"
echo "  • View cron jobs:      crontab -l"
echo "  • Remove cron job:     crontab -e"
echo ""
