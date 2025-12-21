#!/bin/bash
# Yellow Taxi Analytics - Interactive Setup Script
# Menu-driven interface for all common operations

set -e

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Function to display the menu
show_menu() {
    clear
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                       ║${NC}"
    echo -e "${BLUE}║       Yellow Taxi Analytics - Setup Menu             ║${NC}"
    echo -e "${BLUE}║                                                       ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Project Directory:${NC} $PROJECT_DIR"
    echo ""
    echo -e "${BOLD}Choose an option:${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC} - Initial setup (database + sample data 93K rows)"
    echo -e "  ${GREEN}2${NC} - Load full dataset (17.4M rows)"
    echo -e "  ${GREEN}3${NC} - Refresh materialized views (incremental)"
    echo -e "  ${GREEN}4${NC} - Setup daily cron job for MV refresh"
    echo -e "  ${GREEN}5${NC} - Start API server (FastAPI)"
    echo -e "  ${GREEN}6${NC} - Run benchmark (incremental refresh)"
    echo -e "  ${GREEN}7${NC} - Test API endpoints"
    echo -e "  ${GREEN}8${NC} - Check database status"
    echo -e "  ${RED}9${NC} - Exit"
    echo ""
}

# Function to pause and wait for user
pause() {
    echo ""
    echo -e "${CYAN}Press Enter to continue...${NC}"
    read
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice [1-9]: " choice
    echo ""

    case $choice in
        1)
            echo -e "${YELLOW}Running initial setup...${NC}\n"

            # Check if PostgreSQL is running
            if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
                echo -e "${RED}Error: PostgreSQL is not running${NC}"
                echo "Start PostgreSQL and try again"
                pause
                continue
            fi

            # Load environment variables
            if [ ! -f .env ]; then
                echo -e "${RED}Error: .env file not found${NC}"
                echo "Create .env file with database credentials"
                pause
                continue
            fi

            # Run database setup
            echo "Step 1: Setting up database..."
            psql -f sql/setup_database.sql

            echo "Step 2: Creating schema..."
            source .env
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/schema.sql

            echo "Step 3: Creating materialized views..."
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/materialized_views.sql

            echo "Step 4: Adding unique indexes..."
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/add_unique_indexes_for_concurrent_refresh.sql

            echo "Step 5: Creating incremental views..."
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/incremental_materialized_views.sql

            echo "Step 6: Loading zone data..."
            source venv/bin/activate
            python src/etl/load_zones.py

            echo "Step 7: Loading sample ride data (93K rows)..."
            python src/etl/load_data.py

            echo -e "\n${GREEN}✓ Setup complete!${NC}"
            echo ""
            echo "Next steps:"
            echo "  - Run option 2 to load full dataset (17.4M rows)"
            echo "  - Run option 5 to start the API server"
            pause
            ;;

        2)
            echo -e "${YELLOW}Loading full dataset (17.4M rows)...${NC}\n"
            echo "This will take 15-20 minutes"
            echo ""
            read -p "Continue? [y/N]: " confirm

            if [[ $confirm == [yY] ]]; then
                source venv/bin/activate
                python scripts/load_all_data.py

                echo -e "\n${YELLOW}Refreshing materialized views...${NC}"
                bash scripts/refresh_incremental_views.sh

                echo -e "\n${GREEN}✓ Full dataset loaded!${NC}"
                echo "Total rows: 17,417,027"
            else
                echo "Cancelled"
            fi
            pause
            ;;

        3)
            echo -e "${YELLOW}Refreshing materialized views...${NC}\n"
            bash scripts/refresh_incremental_views.sh
            echo -e "\n${GREEN}✓ Refresh complete!${NC}"
            pause
            ;;

        4)
            echo -e "${YELLOW}Setting up daily cron job...${NC}\n"

            # Make script executable
            chmod +x scripts/refresh_incremental_views.sh

            # Add to crontab (daily at 2am)
            CRON_JOB="0 2 * * * $PROJECT_DIR/scripts/refresh_incremental_views.sh >> $PROJECT_DIR/logs/cron_refresh.log 2>&1"

            # Check if job already exists
            if crontab -l 2>/dev/null | grep -q "refresh_incremental_views.sh"; then
                echo -e "${YELLOW}Cron job already exists${NC}"
                echo "Current cron jobs:"
                crontab -l | grep "refresh_incremental_views.sh"
            else
                # Add to crontab
                (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
                echo -e "${GREEN}✓ Cron job added!${NC}"
                echo ""
                echo "Schedule: Daily at 2:00 AM"
                echo "Logs: $PROJECT_DIR/logs/cron_refresh.log"
            fi

            echo ""
            echo "To view all cron jobs: crontab -l"
            echo "To remove cron job: crontab -e (delete the line)"
            pause
            ;;

        5)
            echo -e "${YELLOW}Starting FastAPI server...${NC}\n"
            echo "API will be available at:"
            echo "  - API: http://localhost:8000"
            echo "  - Docs: http://localhost:8000/docs"
            echo "  - ReDoc: http://localhost:8000/redoc"
            echo ""
            echo -e "${CYAN}Press Ctrl+C to stop the server${NC}"
            echo ""
            source venv/bin/activate
            cd src/api
            uvicorn main:app --reload --host 0.0.0.0 --port 8000
            cd ../..
            pause
            ;;

        6)
            echo -e "${YELLOW}Running benchmark...${NC}\n"
            source venv/bin/activate
            python src/analytics/benchmark_incremental_refresh.py
            echo -e "\n${GREEN}✓ Benchmark complete!${NC}"
            echo "Results saved in logs/"
            pause
            ;;

        7)
            echo -e "${YELLOW}Testing API endpoints...${NC}\n"

            if ! bash scripts/test_api.sh 2>/dev/null; then
                echo "Using curl to test endpoints..."

                echo "1. Health check:"
                curl -s http://localhost:8000/health | python -m json.tool
                echo ""

                echo "2. Analytics summary:"
                curl -s http://localhost:8000/api/v1/analytics/summary | python -m json.tool | head -30
                echo ""

                echo "3. Hourly stats (first 3):"
                curl -s "http://localhost:8000/api/v1/analytics/hourly?limit=3" | python -m json.tool
                echo ""

                echo -e "${GREEN}✓ API is working!${NC}"
            fi
            pause
            ;;

        8)
            echo -e "${YELLOW}Checking database status...${NC}\n"
            source .env

            echo "Database connection:"
            if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1" >/dev/null 2>&1; then
                echo -e "  ${GREEN}✓ Connected${NC}"
            else
                echo -e "  ${RED}✗ Cannot connect${NC}"
                pause
                continue
            fi

            echo ""
            echo "Row count:"
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM rides;" | xargs | awk '{printf "  %'"'"'d rows\n", $1}'

            echo ""
            echo "Materialized views:"
            PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
                SELECT
                    schemaname,
                    matviewname as view_name,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
                FROM pg_matviews
                WHERE schemaname = 'public'
                ORDER BY matviewname;
            "

            echo ""
            echo "Last refresh time:"
            if [ -f logs/cron_refresh.log ]; then
                tail -1 logs/cron_refresh.log
            else
                echo "  No cron log found"
            fi
            pause
            ;;

        9)
            echo -e "\n${GREEN}Goodbye!${NC}\n"
            exit 0
            ;;

        *)
            echo -e "${RED}Invalid choice. Please enter a number between 1 and 9.${NC}"
            pause
            ;;
    esac
done
