-- Incremental Materialized View Refresh Strategy
-- Phase 5.2: Hot/Cold Data Partitioning
-- Updated: December 21, 2024
--
-- IMPORTANT: Hot window is based on LATEST DATA in database, not current date
-- This allows proper testing with historical datasets

-- ====================
-- 1. INCREMENTAL HOURLY STATS
-- ====================

-- Cold data: Historical hourly stats (older than 30 days from latest data)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_stats_cold AS
SELECT
    DATE(pickup_datetime) as date,
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    COUNT(CASE WHEN payment_type = 1 THEN 1 END) as credit_card_count,
    COUNT(CASE WHEN payment_type = 2 THEN 1 END) as cash_count
FROM rides
WHERE total_amount > 0
AND dropoff_datetime > pickup_datetime
AND pickup_datetime < (SELECT MAX(pickup_datetime) FROM rides) - INTERVAL '30 days'  -- Historical only
GROUP BY DATE(pickup_datetime), EXTRACT(HOUR FROM pickup_datetime);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_hourly_stats_cold_unique ON mv_hourly_stats_cold(date, hour);

-- Hot data: Recent hourly stats (last 30 days from latest data)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_stats_hot AS
SELECT
    DATE(pickup_datetime) as date,
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    COUNT(CASE WHEN payment_type = 1 THEN 1 END) as credit_card_count,
    COUNT(CASE WHEN payment_type = 2 THEN 1 END) as cash_count
FROM rides
WHERE total_amount > 0
AND dropoff_datetime > pickup_datetime
AND pickup_datetime >= (SELECT MAX(pickup_datetime) FROM rides) - INTERVAL '30 days'  -- Recent only (last 30 days of actual data)
GROUP BY DATE(pickup_datetime), EXTRACT(HOUR FROM pickup_datetime);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_hourly_stats_hot_unique ON mv_hourly_stats_hot(date, hour);

-- Combined view: Union of hot + cold (replaces mv_hourly_stats)
CREATE OR REPLACE VIEW mv_hourly_stats_incremental AS
SELECT * FROM mv_hourly_stats_cold
UNION ALL
SELECT * FROM mv_hourly_stats_hot
ORDER BY date DESC, hour;

COMMENT ON MATERIALIZED VIEW mv_hourly_stats_cold IS 'Historical hourly stats (>30 days old), refreshed weekly';
COMMENT ON MATERIALIZED VIEW mv_hourly_stats_hot IS 'Recent hourly stats (last 30 days), refreshed every 6 hours';
COMMENT ON VIEW mv_hourly_stats_incremental IS 'Combined hourly stats view (hot + cold data)';

-- ====================
-- 2. INCREMENTAL LOCATION STATS
-- ====================

-- Cold: Historical pickup locations
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_pickup_locations_cold AS
SELECT
    r.pickup_location_id,
    z.borough,
    z.zone,
    COUNT(*) as pickup_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration_min
FROM rides r
LEFT JOIN zones z ON r.pickup_location_id = z.location_id
WHERE r.total_amount > 0
AND r.dropoff_datetime > r.pickup_datetime
AND r.pickup_datetime < (SELECT MAX(pickup_datetime) FROM rides) - INTERVAL '30 days'
GROUP BY r.pickup_location_id, z.borough, z.zone;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_pickup_locations_cold_unique ON mv_top_pickup_locations_cold(pickup_location_id);

-- Hot: Recent pickup locations
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_pickup_locations_hot AS
SELECT
    r.pickup_location_id,
    z.borough,
    z.zone,
    COUNT(*) as pickup_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration_min
FROM rides r
LEFT JOIN zones z ON r.pickup_location_id = z.location_id
WHERE r.total_amount > 0
AND r.dropoff_datetime > r.pickup_datetime
AND r.pickup_datetime >= (SELECT MAX(pickup_datetime) FROM rides) - INTERVAL '30 days'
GROUP BY r.pickup_location_id, z.borough, z.zone;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_pickup_locations_hot_unique ON mv_top_pickup_locations_hot(pickup_location_id);

-- Combined view
CREATE OR REPLACE VIEW mv_top_pickup_locations_incremental AS
SELECT
    pickup_location_id,
    borough,
    zone,
    SUM(pickup_count) as pickup_count,
    ROUND(AVG(avg_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(avg_fare)::numeric, 2) as avg_fare,
    SUM(total_revenue) as total_revenue,
    ROUND(AVG(avg_duration_min)::numeric, 2) as avg_duration_min,
    ROUND((SUM(pickup_count) * 100.0 / SUM(SUM(pickup_count)) OVER ())::numeric, 4) as pct_of_total
FROM (
    SELECT * FROM mv_top_pickup_locations_cold
    UNION ALL
    SELECT * FROM mv_top_pickup_locations_hot
) combined
GROUP BY pickup_location_id, borough, zone
ORDER BY pickup_count DESC;

-- ====================
-- 3. INCREMENTAL POPULAR ROUTES
-- ====================

-- Cold: Historical routes
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_routes_cold AS
SELECT
    r.pickup_location_id,
    r.dropoff_location_id,
    z_pickup.zone as pickup_zone,
    z_pickup.borough as pickup_borough,
    z_dropoff.zone as dropoff_zone,
    z_dropoff.borough as dropoff_borough,
    COUNT(*) as trip_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue
FROM rides r
LEFT JOIN zones z_pickup ON r.pickup_location_id = z_pickup.location_id
LEFT JOIN zones z_dropoff ON r.dropoff_location_id = z_dropoff.location_id
WHERE r.total_amount > 0
AND r.dropoff_datetime > r.pickup_datetime
AND r.pickup_datetime < (SELECT MAX(pickup_datetime) FROM rides) - INTERVAL '30 days'
AND z_pickup.zone IS NOT NULL
AND z_dropoff.zone IS NOT NULL
GROUP BY r.pickup_location_id, r.dropoff_location_id,
         z_pickup.zone, z_pickup.borough, z_dropoff.zone, z_dropoff.borough
HAVING COUNT(*) >= 10;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_popular_routes_cold_unique
ON mv_popular_routes_cold(pickup_location_id, dropoff_location_id);

-- Hot: Recent routes
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_routes_hot AS
SELECT
    r.pickup_location_id,
    r.dropoff_location_id,
    z_pickup.zone as pickup_zone,
    z_pickup.borough as pickup_borough,
    z_dropoff.zone as dropoff_zone,
    z_dropoff.borough as dropoff_borough,
    COUNT(*) as trip_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue
FROM rides r
LEFT JOIN zones z_pickup ON r.pickup_location_id = z_pickup.location_id
LEFT JOIN zones z_dropoff ON r.dropoff_location_id = z_dropoff.location_id
WHERE r.total_amount > 0
AND r.dropoff_datetime > r.pickup_datetime
AND r.pickup_datetime >= (SELECT MAX(pickup_datetime) FROM rides) - INTERVAL '30 days'
AND z_pickup.zone IS NOT NULL
AND z_dropoff.zone IS NOT NULL
GROUP BY r.pickup_location_id, r.dropoff_location_id,
         z_pickup.zone, z_pickup.borough, z_dropoff.zone, z_dropoff.borough;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_popular_routes_hot_unique
ON mv_popular_routes_hot(pickup_location_id, dropoff_location_id);

-- Combined view
CREATE OR REPLACE VIEW mv_popular_routes_incremental AS
SELECT
    pickup_location_id,
    dropoff_location_id,
    pickup_zone,
    pickup_borough,
    dropoff_zone,
    dropoff_borough,
    SUM(trip_count) as trip_count,
    ROUND(AVG(avg_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(avg_fare)::numeric, 2) as avg_fare,
    ROUND(AVG(avg_duration_min)::numeric, 2) as avg_duration_min,
    SUM(total_revenue) as total_revenue
FROM (
    SELECT * FROM mv_popular_routes_cold
    UNION ALL
    SELECT * FROM mv_popular_routes_hot
) combined
GROUP BY pickup_location_id, dropoff_location_id, pickup_zone, pickup_borough, dropoff_zone, dropoff_borough
HAVING SUM(trip_count) >= 10
ORDER BY trip_count DESC;

-- ====================
-- 4. REFRESH FUNCTIONS
-- ====================

-- Function to refresh HOT views only (fast, frequent updates)
CREATE OR REPLACE FUNCTION refresh_hot_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_stats_hot;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_pickup_locations_hot;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_routes_hot;
    RAISE NOTICE 'Hot materialized views refreshed at %', now();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_hot_mv() IS 'Refresh only hot (recent 30 days) materialized views - run every 6 hours';

-- Function to refresh COLD views only (slow, infrequent updates)
CREATE OR REPLACE FUNCTION refresh_cold_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_stats_cold;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_pickup_locations_cold;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_routes_cold;
    RAISE NOTICE 'Cold materialized views refreshed at %', now();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_cold_mv() IS 'Refresh only cold (historical >30 days) materialized views - run weekly';

-- Function to refresh ALL incremental views (initial setup or full refresh)
CREATE OR REPLACE FUNCTION refresh_all_incremental_mv()
RETURNS void AS $$
BEGIN
    PERFORM refresh_cold_mv();
    PERFORM refresh_hot_mv();
    RAISE NOTICE 'All incremental materialized views refreshed at %', now();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_incremental_mv() IS 'Refresh all incremental materialized views (hot + cold) - run after bulk data loads';

-- ====================
-- 5. MIGRATION HELPER
-- ====================

-- View to compare old vs new approach
CREATE OR REPLACE VIEW mv_refresh_comparison AS
SELECT
    'Full Refresh' as strategy,
    (SELECT pg_size_pretty(pg_total_relation_size('mv_hourly_stats'))) as view_size,
    'All data' as data_scope,
    'Slow at scale' as performance
UNION ALL
SELECT
    'Incremental (Hot Only)' as strategy,
    (SELECT pg_size_pretty(pg_total_relation_size('mv_hourly_stats_hot'))) as view_size,
    'Last 30 days' as data_scope,
    'Fast at scale' as performance
UNION ALL
SELECT
    'Incremental (Cold)' as strategy,
    (SELECT pg_size_pretty(pg_total_relation_size('mv_hourly_stats_cold'))) as view_size,
    'Historical' as data_scope,
    'Slow but infrequent' as performance;

-- ====================
-- USAGE EXAMPLES
-- ====================

-- Initial setup (run once):
-- SELECT refresh_all_incremental_mv();

-- Regular updates (every 6 hours):
-- SELECT refresh_hot_mv();

-- Historical updates (weekly or after bulk loads):
-- SELECT refresh_cold_mv();

-- Query examples using incremental views:
-- SELECT * FROM mv_hourly_stats_incremental ORDER BY date DESC LIMIT 100;
-- SELECT * FROM mv_top_pickup_locations_incremental ORDER BY pickup_count DESC LIMIT 20;
-- SELECT * FROM mv_popular_routes_incremental ORDER BY trip_count DESC LIMIT 20;

-- Performance comparison:
-- SELECT * FROM mv_refresh_comparison;

-- ====================
-- EXPECTED BENEFITS
-- ====================

-- Dataset Size | Old Refresh Time | Hot Refresh Time | Speedup
-- -------------|------------------|------------------|--------
-- 93K rows     | 0.65s            | 0.65s            | 1x (no benefit yet)
-- 500K rows    | 3.5s             | 0.7s             | 5x faster
-- 1M rows      | 7s               | 0.7s             | 10x faster
-- 3M rows      | 21s              | 0.8s             | 26x faster
-- 10M rows     | 70s              | 1.0s             | 70x faster
--
-- Cold views refreshed weekly (off-peak hours)
-- Hot views refreshed every 6 hours (fast, non-blocking)
