-- Materialized Views for NYC Taxi Analytics
-- City Rides Analytics Dashboard
-- Created: November 8, 2025
-- Purpose: Pre-compute common aggregations for faster query performance

-- ====================
-- 1. HOURLY STATISTICS
-- ====================

-- Hourly trip statistics (refreshed daily)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_stats AS
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
GROUP BY DATE(pickup_datetime), EXTRACT(HOUR FROM pickup_datetime);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_mv_hourly_stats_date ON mv_hourly_stats(date);
CREATE INDEX IF NOT EXISTS idx_mv_hourly_stats_hour ON mv_hourly_stats(hour);

COMMENT ON MATERIALIZED VIEW mv_hourly_stats IS 'Pre-aggregated hourly statistics for rides';

-- ====================
-- 2. LOCATION STATISTICS
-- ====================

-- Top pickup locations with detailed stats
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_pickup_locations AS
SELECT
    r.pickup_location_id,
    z.borough,
    z.zone,
    COUNT(*) as pickup_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 4) as pct_of_total
FROM rides r
LEFT JOIN zones z ON r.pickup_location_id = z.location_id
WHERE r.total_amount > 0
AND r.dropoff_datetime > r.pickup_datetime
GROUP BY r.pickup_location_id, z.borough, z.zone;

CREATE INDEX IF NOT EXISTS idx_mv_pickup_locations_count ON mv_top_pickup_locations(pickup_count DESC);
CREATE INDEX IF NOT EXISTS idx_mv_pickup_locations_borough ON mv_top_pickup_locations(borough);

COMMENT ON MATERIALIZED VIEW mv_top_pickup_locations IS 'Aggregated statistics by pickup location';

-- Top dropoff locations
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_dropoff_locations AS
SELECT
    r.dropoff_location_id,
    z.borough,
    z.zone,
    COUNT(*) as dropoff_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 4) as pct_of_total
FROM rides r
LEFT JOIN zones z ON r.dropoff_location_id = z.location_id
WHERE r.total_amount > 0
GROUP BY r.dropoff_location_id, z.borough, z.zone;

CREATE INDEX IF NOT EXISTS idx_mv_dropoff_locations_count ON mv_top_dropoff_locations(dropoff_count DESC);

COMMENT ON MATERIALIZED VIEW mv_top_dropoff_locations IS 'Aggregated statistics by dropoff location';

-- ====================
-- 3. VENDOR PERFORMANCE
-- ====================

-- Daily vendor performance metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vendor_daily_performance AS
SELECT
    DATE(r.pickup_datetime) as date,
    v.vendor_name,
    v.vendor_id,
    COUNT(*) as trip_count,
    ROUND(SUM(r.total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration,
    COUNT(CASE WHEN r.payment_type = 1 THEN 1 END) as credit_card_trips,
    ROUND(AVG(CASE WHEN r.payment_type = 1 THEN r.tip_amount END)::numeric, 2) as avg_tip
FROM rides r
JOIN vendors v ON r.vendor_id = v.vendor_id
WHERE r.total_amount > 0
AND r.dropoff_datetime > r.pickup_datetime
GROUP BY DATE(r.pickup_datetime), v.vendor_name, v.vendor_id;

CREATE INDEX IF NOT EXISTS idx_mv_vendor_daily_date ON mv_vendor_daily_performance(date);
CREATE INDEX IF NOT EXISTS idx_mv_vendor_daily_vendor ON mv_vendor_daily_performance(vendor_id);

COMMENT ON MATERIALIZED VIEW mv_vendor_daily_performance IS 'Daily performance metrics by vendor';

-- ====================
-- 4. PAYMENT ANALYSIS
-- ====================

-- Payment type breakdown by hour
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_payment_hourly AS
SELECT
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Other'
    END as payment_method,
    payment_type,
    COUNT(*) as trip_count,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(CASE WHEN payment_type = 1 THEN tip_amount END)::numeric, 2) as avg_tip
FROM rides
WHERE total_amount > 0
GROUP BY EXTRACT(HOUR FROM pickup_datetime), payment_type;

CREATE INDEX IF NOT EXISTS idx_mv_payment_hourly_hour ON mv_payment_hourly(hour);

COMMENT ON MATERIALIZED VIEW mv_payment_hourly IS 'Payment type distribution by hour';

-- ====================
-- 5. TRIP DISTANCE SEGMENTS
-- ====================

-- Trip statistics by distance segments
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_distance_segments AS
SELECT
    CASE
        WHEN trip_distance < 1 THEN '0-1 miles'
        WHEN trip_distance < 2 THEN '1-2 miles'
        WHEN trip_distance < 5 THEN '2-5 miles'
        WHEN trip_distance < 10 THEN '5-10 miles'
        WHEN trip_distance < 20 THEN '10-20 miles'
        ELSE '20+ miles'
    END as distance_segment,
    COUNT(*) as trip_count,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(MIN(total_amount)::numeric, 2) as min_fare,
    ROUND(MAX(total_amount)::numeric, 2) as max_fare,
    ROUND(AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as median_fare,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 2) as pct_of_total
FROM rides
WHERE total_amount > 0
AND trip_distance > 0
AND dropoff_datetime > pickup_datetime
GROUP BY CASE
        WHEN trip_distance < 1 THEN '0-1 miles'
        WHEN trip_distance < 2 THEN '1-2 miles'
        WHEN trip_distance < 5 THEN '2-5 miles'
        WHEN trip_distance < 10 THEN '5-10 miles'
        WHEN trip_distance < 20 THEN '10-20 miles'
        ELSE '20+ miles'
    END;

COMMENT ON MATERIALIZED VIEW mv_distance_segments IS 'Trip statistics segmented by distance ranges';

-- ====================
-- 6. POPULAR ROUTES
-- ====================

-- Most popular routes (pickup-dropoff pairs)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_popular_routes AS
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
AND z_pickup.zone IS NOT NULL
AND z_dropoff.zone IS NOT NULL
GROUP BY r.pickup_location_id, r.dropoff_location_id,
         z_pickup.zone, z_pickup.borough, z_dropoff.zone, z_dropoff.borough
HAVING COUNT(*) >= 10;  -- Minimum threshold for statistical significance

CREATE INDEX IF NOT EXISTS idx_mv_popular_routes_count ON mv_popular_routes(trip_count DESC);
CREATE INDEX IF NOT EXISTS idx_mv_popular_routes_pickup ON mv_popular_routes(pickup_location_id);
CREATE INDEX IF NOT EXISTS idx_mv_popular_routes_dropoff ON mv_popular_routes(dropoff_location_id);

COMMENT ON MATERIALIZED VIEW mv_popular_routes IS 'Most frequently traveled routes with statistics';

-- ====================
-- 7. TIME-BASED PATTERNS
-- ====================

-- Day of week and hour patterns
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_time_patterns AS
SELECT
    EXTRACT(DOW FROM pickup_datetime) as day_of_week,
    TO_CHAR(pickup_datetime, 'Day') as day_name,
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    COUNT(CASE WHEN payment_type = 1 THEN 1 END) as credit_card_count
FROM rides
WHERE total_amount > 0
GROUP BY EXTRACT(DOW FROM pickup_datetime), TO_CHAR(pickup_datetime, 'Day'), EXTRACT(HOUR FROM pickup_datetime);

CREATE INDEX IF NOT EXISTS idx_mv_time_patterns_dow ON mv_time_patterns(day_of_week);
CREATE INDEX IF NOT EXISTS idx_mv_time_patterns_hour ON mv_time_patterns(hour);

COMMENT ON MATERIALIZED VIEW mv_time_patterns IS 'Trip patterns by day of week and hour';

-- ====================
-- 8. ANALYTICS SUMMARY
-- ====================

-- Overall analytics summary for fast dashboard queries
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analytics_summary AS
SELECT
    COUNT(*) as total_trips,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60)::numeric, 2) as avg_duration_min,
    MIN(pickup_datetime) as date_range_start,
    MAX(dropoff_datetime) as date_range_end
FROM rides
WHERE
    total_amount > 0
    AND dropoff_datetime > pickup_datetime;

CREATE INDEX IF NOT EXISTS idx_mv_analytics_summary_trips ON mv_analytics_summary(total_trips);

COMMENT ON MATERIALIZED VIEW mv_analytics_summary IS 'Pre-computed overall analytics summary for fast dashboard loading';

-- ====================
-- REFRESH FUNCTIONS
-- ====================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_mv()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hourly_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_pickup_locations;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_dropoff_locations;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_vendor_daily_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_payment_hourly;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_distance_segments;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_popular_routes;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_time_patterns;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_analytics_summary;
    RAISE NOTICE 'All materialized views refreshed successfully at %', now();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_all_mv() IS 'Refresh all materialized views with concurrent option';

-- ====================
-- USAGE EXAMPLES
-- ====================

-- Query examples using materialized views:

-- 1. Get top 10 pickup locations
-- SELECT * FROM mv_top_pickup_locations ORDER BY pickup_count DESC LIMIT 10;

-- 2. Daily vendor comparison
-- SELECT * FROM mv_vendor_daily_performance WHERE date = CURRENT_DATE - 1;

-- 3. Hourly revenue trend
-- SELECT hour, SUM(total_revenue) as revenue FROM mv_hourly_stats GROUP BY hour ORDER BY hour;

-- 4. Most popular routes
-- SELECT * FROM mv_popular_routes ORDER BY trip_count DESC LIMIT 20;

-- 5. Payment patterns by time
-- SELECT hour, payment_method, trip_count FROM mv_payment_hourly ORDER BY hour, payment_method;

-- To refresh views after new data is loaded:
-- SELECT refresh_all_mv();
