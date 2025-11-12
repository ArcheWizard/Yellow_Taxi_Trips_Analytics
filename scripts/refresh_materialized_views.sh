#!/bin/bash
# Refresh Materialized Views Script
# This script refreshes all materialized views to ensure dashboards show current data

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database connection details
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-city_rides_db}"
DB_USER="${DB_USER:-rides_user}"

echo "========================================="
echo "Refreshing Materialized Views"
echo "========================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo ""

# List of materialized views to refresh
VIEWS=(
    "mv_hourly_stats"
    "mv_top_pickup_locations"
    "mv_top_dropoff_locations"
    "mv_vendor_daily_performance"
    "mv_payment_hourly"
    "mv_distance_segments"
    "mv_time_patterns"
    "mv_popular_routes"
    "mv_analytics_summary"
)

# Function to refresh a single view
refresh_view() {
    local view_name=$1
    echo -n "Refreshing $view_name... "

    start_time=$(date +%s)

    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -c "REFRESH MATERIALIZED VIEW $view_name;" \
        -q 2>/dev/null

    if [ $? -eq 0 ]; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo "✓ Done (${duration}s)"
    else
        echo "✗ Failed"
        return 1
    fi
}

# Track statistics
total_views=${#VIEWS[@]}
success_count=0
fail_count=0
start_all=$(date +%s)

# Refresh all views
for view in "${VIEWS[@]}"; do
    if refresh_view "$view"; then
        ((success_count++))
    else
        ((fail_count++))
    fi
done

end_all=$(date +%s)
total_duration=$((end_all - start_all))

echo ""
echo "========================================="
echo "Refresh Complete"
echo "========================================="
echo "Total views: $total_views"
echo "Successful: $success_count"
echo "Failed: $fail_count"
echo "Total time: ${total_duration}s"
echo ""

# Add benchmarking
echo "Benchmark Results:" >> /tmp/mv_refresh.log
echo "Total views: $total_views" >> /tmp/mv_refresh.log
echo "Total duration: ${total_duration}s" >> /tmp/mv_refresh.log
echo "Avg per view: $((total_duration / total_views))s" >> /tmp/mv_refresh.log

if [ $fail_count -gt 0 ]; then
    echo "⚠️  Some views failed to refresh"
    exit 1
else
    echo "✅ All views refreshed successfully"
    exit 0
fi
