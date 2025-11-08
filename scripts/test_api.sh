#!/bin/bash
# API Testing Script
# Tests all endpoints of the City Rides Analytics API

BASE_URL="http://localhost:8000"

echo "========================================="
echo "Testing City Rides Analytics API"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local url=$2

    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC} ($response)"
    else
        echo -e "${RED}✗ FAILED${NC} ($response)"
    fi
}

# Health Check Endpoints
echo "1. Health Check Endpoints"
test_endpoint "Root endpoint" "$BASE_URL/"
test_endpoint "Health check" "$BASE_URL/health"
echo ""

# Rides Endpoints
echo "2. Rides Endpoints"
test_endpoint "Get rides (paginated)" "$BASE_URL/api/v1/rides?limit=10"
test_endpoint "Get rides (with filters)" "$BASE_URL/api/v1/rides?limit=5&vendor_id=1"
test_endpoint "Get ride by ID" "$BASE_URL/api/v1/rides/90722"
echo ""

# Analytics Endpoints
echo "3. Analytics Endpoints"
test_endpoint "Analytics summary" "$BASE_URL/api/v1/analytics/summary"
test_endpoint "Hourly stats" "$BASE_URL/api/v1/analytics/hourly?limit=5"
test_endpoint "Top pickup locations" "$BASE_URL/api/v1/analytics/locations/pickup?limit=5"
test_endpoint "Top dropoff locations" "$BASE_URL/api/v1/analytics/locations/dropoff?limit=5"
test_endpoint "Vendor performance" "$BASE_URL/api/v1/analytics/vendors/performance?limit=5"
test_endpoint "Payment hourly stats" "$BASE_URL/api/v1/analytics/payment/hourly"
test_endpoint "Distance segments" "$BASE_URL/api/v1/analytics/distance/segments"
test_endpoint "Time patterns" "$BASE_URL/api/v1/analytics/patterns/time?limit=24"
test_endpoint "Popular routes" "$BASE_URL/api/v1/analytics/routes/popular?limit=5"
echo ""

echo "========================================="
echo "Testing Complete!"
echo "========================================="
echo ""
echo "View API documentation at: $BASE_URL/docs"
echo "View ReDoc documentation at: $BASE_URL/redoc"
