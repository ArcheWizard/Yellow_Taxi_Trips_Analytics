-- Advanced Analytics Queries for NYC Taxi Data
-- City Rides Analytics Dashboard
-- Created: November 8, 2025
-- Features: Window Functions, CTEs, Subqueries, Advanced Aggregations

-- ====================
-- 1. RANKING & WINDOW FUNCTIONS
-- ====================

-- Top 5 most expensive trips per vendor
WITH ranked_trips AS (
    SELECT
        r.ride_id,
        v.vendor_name,
        r.pickup_datetime,
        r.trip_distance,
        r.total_amount,
        ROW_NUMBER() OVER (PARTITION BY v.vendor_name ORDER BY r.total_amount DESC) as rank
    FROM rides r
    JOIN vendors v ON r.vendor_id = v.vendor_id
    WHERE r.total_amount > 0
)
SELECT
    vendor_name,
    ride_id,
    pickup_datetime,
    trip_distance,
    ROUND(total_amount::numeric, 2) as total_amount,
    rank
FROM ranked_trips
WHERE rank <= 5
ORDER BY vendor_name, rank;

-- Daily revenue with running total
WITH daily_revenue AS (
    SELECT
        DATE(pickup_datetime) as date,
        COUNT(*) as trips,
        SUM(total_amount) as revenue
    FROM rides
    GROUP BY DATE(pickup_datetime)
)
SELECT
    date,
    trips,
    ROUND(revenue::numeric, 2) as daily_revenue,
    ROUND(SUM(revenue) OVER (ORDER BY date)::numeric, 2) as running_total,
    ROUND(AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)::numeric, 2) as moving_avg_3day
FROM daily_revenue
ORDER BY date;

-- Percentile analysis of fares
SELECT
    ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as p10,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as p75,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as p90,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as p95,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as p99
FROM rides
WHERE total_amount > 0;

-- ====================
-- 2. COHORT ANALYSIS
-- ====================

-- Hour-over-hour comparison (current hour vs same hour previous day)
WITH hourly_stats AS (
    SELECT
        DATE(pickup_datetime) as date,
        EXTRACT(HOUR FROM pickup_datetime) as hour,
        COUNT(*) as trips,
        AVG(total_amount) as avg_fare,
        AVG(trip_distance) as avg_distance
    FROM rides
    GROUP BY DATE(pickup_datetime), EXTRACT(HOUR FROM pickup_datetime)
)
SELECT
    h1.date,
    h1.hour,
    h1.trips as current_trips,
    h2.trips as previous_day_trips,
    ROUND(((h1.trips - h2.trips) * 100.0 / NULLIF(h2.trips, 0))::numeric, 2) as trip_growth_pct,
    ROUND(h1.avg_fare::numeric, 2) as current_avg_fare,
    ROUND(h2.avg_fare::numeric, 2) as previous_avg_fare,
    ROUND(((h1.avg_fare - h2.avg_fare) * 100.0 / NULLIF(h2.avg_fare, 0))::numeric, 2) as fare_change_pct
FROM hourly_stats h1
LEFT JOIN hourly_stats h2 ON h1.hour = h2.hour AND h1.date = h2.date + 1
WHERE h2.date IS NOT NULL
ORDER BY h1.date, h1.hour;

-- ====================
-- 3. GEOSPATIAL ANALYSIS
-- ====================

-- Airport traffic patterns
WITH airport_zones AS (
    SELECT location_id, zone
    FROM zones
    WHERE zone IN ('JFK Airport', 'LaGuardia Airport', 'Newark Airport')
)
SELECT
    az.zone as airport,
    EXTRACT(HOUR FROM r.pickup_datetime) as hour,
    COUNT(*) as pickup_count,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60)::numeric, 2) as avg_duration_min
FROM rides r
JOIN airport_zones az ON r.pickup_location_id = az.location_id
GROUP BY az.zone, EXTRACT(HOUR FROM r.pickup_datetime)
ORDER BY az.zone, hour;

-- Borough-to-borough flow analysis
WITH borough_pairs AS (
    SELECT
        z_pickup.borough as from_borough,
        z_dropoff.borough as to_borough,
        COUNT(*) as trip_count,
        AVG(r.total_amount) as avg_fare,
        AVG(r.trip_distance) as avg_distance,
        AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60) as avg_duration
    FROM rides r
    JOIN zones z_pickup ON r.pickup_location_id = z_pickup.location_id
    JOIN zones z_dropoff ON r.dropoff_location_id = z_dropoff.location_id
    WHERE z_pickup.borough IS NOT NULL AND z_dropoff.borough IS NOT NULL
    GROUP BY z_pickup.borough, z_dropoff.borough
)
SELECT
    from_borough,
    to_borough,
    trip_count,
    ROUND(avg_fare::numeric, 2) as avg_fare,
    ROUND(avg_distance::numeric, 2) as avg_distance_miles,
    ROUND(avg_duration::numeric, 2) as avg_duration_min,
    ROUND((trip_count * 100.0 / SUM(trip_count) OVER ())::numeric, 2) as pct_of_total
FROM borough_pairs
WHERE trip_count > 10  -- Filter noise
ORDER BY trip_count DESC
LIMIT 20;

-- ====================
-- 4. TIME SERIES ANALYSIS
-- ====================

-- Hourly trends with statistical measures
WITH hourly_metrics AS (
    SELECT
        EXTRACT(HOUR FROM pickup_datetime) as hour,
        COUNT(*) as trip_count,
        AVG(total_amount) as avg_fare,
        STDDEV(total_amount) as stddev_fare,
        MIN(total_amount) as min_fare,
        MAX(total_amount) as max_fare
    FROM rides
    WHERE total_amount > 0
    GROUP BY EXTRACT(HOUR FROM pickup_datetime)
)
SELECT
    hour,
    trip_count,
    ROUND(avg_fare::numeric, 2) as avg_fare,
    ROUND(stddev_fare::numeric, 2) as stddev_fare,
    ROUND((stddev_fare / NULLIF(avg_fare, 0) * 100)::numeric, 2) as coefficient_of_variation,
    ROUND(min_fare::numeric, 2) as min_fare,
    ROUND(max_fare::numeric, 2) as max_fare,
    ROUND((max_fare - min_fare)::numeric, 2) as fare_range
FROM hourly_metrics
ORDER BY hour;

-- Day of week patterns with comparison to overall average
WITH overall_avg AS (
    SELECT AVG(total_amount) as avg_fare
    FROM rides
    WHERE total_amount > 0
),
dow_stats AS (
    SELECT
        TO_CHAR(pickup_datetime, 'Day') as day_name,
        EXTRACT(DOW FROM pickup_datetime) as day_num,
        COUNT(*) as trip_count,
        AVG(total_amount) as avg_fare,
        AVG(trip_distance) as avg_distance
    FROM rides
    WHERE total_amount > 0
    GROUP BY TO_CHAR(pickup_datetime, 'Day'), EXTRACT(DOW FROM pickup_datetime)
)
SELECT
    day_name,
    trip_count,
    ROUND(avg_fare::numeric, 2) as avg_fare,
    ROUND((SELECT avg_fare FROM overall_avg)::numeric, 2) as overall_avg_fare,
    ROUND(((avg_fare - (SELECT avg_fare FROM overall_avg)) / (SELECT avg_fare FROM overall_avg) * 100)::numeric, 2) as pct_diff_from_avg,
    ROUND(avg_distance::numeric, 2) as avg_distance
FROM dow_stats
ORDER BY day_num;

-- ====================
-- 5. CUSTOMER BEHAVIOR ANALYSIS
-- ====================

-- Tip behavior by trip characteristics
WITH trip_segments AS (
    SELECT
        CASE
            WHEN fare_amount < 10 THEN 'Short ($0-10)'
            WHEN fare_amount < 20 THEN 'Medium ($10-20)'
            WHEN fare_amount < 50 THEN 'Long ($20-50)'
            ELSE 'Very Long ($50+)'
        END as trip_segment,
        CASE
            WHEN EXTRACT(HOUR FROM pickup_datetime) BETWEEN 6 AND 9 THEN 'Morning Rush'
            WHEN EXTRACT(HOUR FROM pickup_datetime) BETWEEN 17 AND 20 THEN 'Evening Rush'
            WHEN EXTRACT(HOUR FROM pickup_datetime) BETWEEN 22 AND 4 THEN 'Late Night'
            ELSE 'Off-Peak'
        END as time_segment,
        fare_amount,
        tip_amount,
        total_amount
    FROM rides
    WHERE payment_type = 1  -- Credit card only (shows tips)
    AND fare_amount > 0
)
SELECT
    trip_segment,
    time_segment,
    COUNT(*) as trip_count,
    ROUND(AVG(fare_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(tip_amount)::numeric, 2) as avg_tip,
    ROUND(AVG(tip_amount / NULLIF(fare_amount, 0) * 100)::numeric, 2) as avg_tip_pct,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY tip_amount / NULLIF(fare_amount, 0) * 100)::numeric, 2) as median_tip_pct
FROM trip_segments
GROUP BY trip_segment, time_segment
ORDER BY trip_segment, time_segment;

-- Payment type distribution by trip characteristics
SELECT
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Other'
    END as payment_method,
    CASE
        WHEN trip_distance < 2 THEN '< 2 miles'
        WHEN trip_distance < 5 THEN '2-5 miles'
        WHEN trip_distance < 10 THEN '5-10 miles'
        ELSE '10+ miles'
    END as distance_range,
    COUNT(*) as trip_count,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 2) as pct_of_total
FROM rides
WHERE total_amount > 0
GROUP BY payment_type,
    CASE
        WHEN trip_distance < 2 THEN '< 2 miles'
        WHEN trip_distance < 5 THEN '2-5 miles'
        WHEN trip_distance < 10 THEN '5-10 miles'
        ELSE '10+ miles'
    END
ORDER BY payment_type, MIN(trip_distance);

-- ====================
-- 6. VENDOR PERFORMANCE COMPARISON
-- ====================

-- Comprehensive vendor metrics
WITH vendor_metrics AS (
    SELECT
        v.vendor_name,
        COUNT(*) as total_trips,
        SUM(r.total_amount) as total_revenue,
        AVG(r.total_amount) as avg_fare,
        AVG(r.trip_distance) as avg_distance,
        AVG(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60) as avg_duration,
        AVG(r.trip_distance / NULLIF(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/3600, 0)) as avg_speed,
        COUNT(CASE WHEN r.payment_type = 1 THEN 1 END) as credit_card_trips,
        AVG(CASE WHEN r.payment_type = 1 THEN r.tip_amount END) as avg_tip
    FROM rides r
    JOIN vendors v ON r.vendor_id = v.vendor_id
    WHERE r.total_amount > 0
    AND r.dropoff_datetime > r.pickup_datetime
    GROUP BY v.vendor_name
)
SELECT
    vendor_name,
    total_trips,
    ROUND(total_revenue::numeric, 2) as total_revenue,
    ROUND(avg_fare::numeric, 2) as avg_fare,
    ROUND(avg_distance::numeric, 2) as avg_distance_miles,
    ROUND(avg_duration::numeric, 2) as avg_duration_min,
    ROUND(avg_speed::numeric, 2) as avg_speed_mph,
    credit_card_trips,
    ROUND((credit_card_trips * 100.0 / total_trips)::numeric, 2) as credit_card_pct,
    ROUND(avg_tip::numeric, 2) as avg_tip_cc_only
FROM vendor_metrics
ORDER BY total_trips DESC;

-- ====================
-- 7. OUTLIER DETECTION
-- ====================

-- Identify unusual trips (potential data quality issues or interesting patterns)
WITH trip_stats AS (
    SELECT
        AVG(total_amount) as avg_fare,
        STDDEV(total_amount) as stddev_fare,
        AVG(trip_distance) as avg_distance,
        STDDEV(trip_distance) as stddev_distance
    FROM rides
    WHERE total_amount > 0
)
SELECT
    r.ride_id,
    r.pickup_datetime,
    r.trip_distance,
    r.total_amount,
    ROUND(EXTRACT(EPOCH FROM (r.dropoff_datetime - r.pickup_datetime))/60::numeric, 2) as duration_min,
    ROUND((r.total_amount - ts.avg_fare) / NULLIF(ts.stddev_fare, 0)::numeric, 2) as fare_z_score,
    ROUND((r.trip_distance - ts.avg_distance) / NULLIF(ts.stddev_distance, 0)::numeric, 2) as distance_z_score,
    CASE
        WHEN ABS((r.total_amount - ts.avg_fare) / NULLIF(ts.stddev_fare, 0)) > 3 THEN 'Fare Outlier'
        WHEN ABS((r.trip_distance - ts.avg_distance) / NULLIF(ts.stddev_distance, 0)) > 3 THEN 'Distance Outlier'
        ELSE 'Normal'
    END as outlier_type
FROM rides r
CROSS JOIN trip_stats ts
WHERE r.total_amount > 0
AND (
    ABS((r.total_amount - ts.avg_fare) / NULLIF(ts.stddev_fare, 0)) > 3
    OR ABS((r.trip_distance - ts.avg_distance) / NULLIF(ts.stddev_distance, 0)) > 3
)
ORDER BY ABS((r.total_amount - ts.avg_fare) / NULLIF(ts.stddev_fare, 0)) DESC
LIMIT 20;

-- ====================
-- 8. EFFICIENCY METRICS
-- ====================

-- Revenue per mile by hour and zone
WITH efficiency_metrics AS (
    SELECT
        EXTRACT(HOUR FROM r.pickup_datetime) as hour,
        z.borough,
        COUNT(*) as trip_count,
        SUM(r.total_amount) as total_revenue,
        SUM(r.trip_distance) as total_distance,
        SUM(r.total_amount) / NULLIF(SUM(r.trip_distance), 0) as revenue_per_mile
    FROM rides r
    LEFT JOIN zones z ON r.pickup_location_id = z.location_id
    WHERE r.total_amount > 0 AND r.trip_distance > 0
    AND z.borough IS NOT NULL
    GROUP BY EXTRACT(HOUR FROM r.pickup_datetime), z.borough
)
SELECT
    hour,
    borough,
    trip_count,
    ROUND(total_revenue::numeric, 2) as total_revenue,
    ROUND(total_distance::numeric, 2) as total_miles,
    ROUND(revenue_per_mile::numeric, 2) as revenue_per_mile
FROM efficiency_metrics
WHERE trip_count >= 10  -- Minimum sample size
ORDER BY revenue_per_mile DESC
LIMIT 25;

-- ====================
-- 9. DEMAND FORECASTING DATA
-- ====================

-- Historical patterns for forecasting
WITH demand_patterns AS (
    SELECT
        DATE(pickup_datetime) as date,
        EXTRACT(DOW FROM pickup_datetime) as day_of_week,
        EXTRACT(HOUR FROM pickup_datetime) as hour,
        COUNT(*) as trip_count,
        AVG(total_amount) as avg_fare
    FROM rides
    GROUP BY DATE(pickup_datetime),
             EXTRACT(DOW FROM pickup_datetime),
             EXTRACT(HOUR FROM pickup_datetime)
)
SELECT
    day_of_week,
    TO_CHAR(TO_TIMESTAMP(day_of_week * 86400), 'Day') as day_name,
    hour,
    ROUND(AVG(trip_count)::numeric, 0) as avg_trips,
    ROUND(STDDEV(trip_count)::numeric, 2) as stddev_trips,
    ROUND(MIN(trip_count)::numeric, 0) as min_trips,
    ROUND(MAX(trip_count)::numeric, 0) as max_trips,
    ROUND(AVG(avg_fare)::numeric, 2) as avg_fare
FROM demand_patterns
GROUP BY day_of_week, hour
ORDER BY day_of_week, hour;
