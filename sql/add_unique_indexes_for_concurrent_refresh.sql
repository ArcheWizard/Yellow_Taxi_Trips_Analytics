-- Add Unique Indexes to Materialized Views for Concurrent Refresh
-- Created: December 21, 2024
-- Purpose: Enable CONCURRENTLY option for materialized view refreshes
--          (avoids locking during refresh operations)

-- ====================
-- 1. HOURLY STATISTICS
-- ====================
-- Unique on (date, hour) since each combination is unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_hourly_stats_unique
ON mv_hourly_stats(date, hour);

-- ====================
-- 2. TOP PICKUP LOCATIONS
-- ====================
-- Unique on pickup_location_id since each location appears once
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_pickup_locations_unique
ON mv_top_pickup_locations(pickup_location_id);

-- ====================
-- 3. TOP DROPOFF LOCATIONS
-- ====================
-- Unique on dropoff_location_id since each location appears once
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dropoff_locations_unique
ON mv_top_dropoff_locations(dropoff_location_id);

-- ====================
-- 4. VENDOR DAILY PERFORMANCE
-- ====================
-- Unique on (date, vendor_id) since each vendor has one row per date
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_vendor_daily_unique
ON mv_vendor_daily_performance(date, vendor_id);

-- ====================
-- 5. PAYMENT HOURLY
-- ====================
-- Unique on (hour, payment_type) since each combination is unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_payment_hourly_unique
ON mv_payment_hourly(hour, payment_type);

-- ====================
-- 6. DISTANCE SEGMENTS
-- ====================
-- Unique on distance_segment since each segment appears once
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_distance_segments_unique
ON mv_distance_segments(distance_segment);

-- ====================
-- 7. TIME PATTERNS
-- ====================
-- Unique on (day_of_week, hour) since each combination is unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_time_patterns_unique
ON mv_time_patterns(day_of_week, hour);

-- ====================
-- 8. POPULAR ROUTES
-- ====================
-- Unique on (pickup_location_id, dropoff_location_id) since each route is unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_popular_routes_unique
ON mv_popular_routes(pickup_location_id, dropoff_location_id);

-- ====================
-- 9. ANALYTICS SUMMARY
-- ====================
-- This view already has a unique index (only 1 row, but PostgreSQL needs an index)
-- We'll add a dummy column-based unique index
-- Since there's only 1 row, we can use any column
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_analytics_summary_unique
ON mv_analytics_summary(total_trips);

-- ====================
-- VERIFICATION
-- ====================

-- Verify all unique indexes were created
SELECT
    schemaname,
    tablename as view_name,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename LIKE 'mv_%'
  AND indexdef LIKE '%UNIQUE%'
ORDER BY tablename, indexname;

-- Test concurrent refresh (should work now)
-- Uncomment to test:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_stats;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_pickup_locations;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_dropoff_locations;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_vendor_daily_performance;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_payment_hourly;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_distance_segments;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_time_patterns;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_routes;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_analytics_summary;
