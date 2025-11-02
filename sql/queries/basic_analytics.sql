-- Basic Analytics Queries for NYC Taxi Data
-- City Rides Analytics Dashboard
-- Created: November 2, 2025

-- ====================
-- 1. TRIP VOLUME ANALYSIS
-- ====================

-- Total trips loaded
SELECT COUNT(*) as total_trips
FROM rides;

-- Trips by vendor
SELECT
    v.vendor_name,
    COUNT(*) as trip_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM rides r
JOIN vendors v ON r.vendor_id = v.vendor_id
GROUP BY v.vendor_name
ORDER BY trip_count DESC;

-- Trips by hour of day
SELECT
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
GROUP BY hour
ORDER BY hour;

-- Trips by day of week
SELECT
    TO_CHAR(pickup_datetime, 'Day') as day_name,
    EXTRACT(DOW FROM pickup_datetime) as day_num,
    COUNT(*) as trip_count,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
GROUP BY day_name, day_num
ORDER BY day_num;

-- ====================
-- 2. FINANCIAL ANALYSIS
-- ====================

-- Revenue summary
SELECT
    COUNT(*) as total_trips,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(MIN(total_amount)::numeric, 2) as min_fare,
    ROUND(MAX(total_amount)::numeric, 2) as max_fare,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_amount)::numeric, 2) as median_fare
FROM rides
WHERE total_amount > 0;

-- Revenue by payment type
SELECT
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        WHEN 5 THEN 'Unknown'
        WHEN 6 THEN 'Voided'
        ELSE 'Other'
    END as payment_method,
    COUNT(*) as trip_count,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(AVG(tip_amount)::numeric, 2) as avg_tip
FROM rides
GROUP BY payment_type
ORDER BY total_revenue DESC;

-- Daily revenue trend
SELECT
    DATE(pickup_datetime) as date,
    COUNT(*) as trips,
    ROUND(SUM(total_amount)::numeric, 2) as revenue,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
GROUP BY date
ORDER BY date;

-- ====================
-- 3. DISTANCE & DURATION
-- ====================

-- Trip distance distribution
SELECT
    CASE
        WHEN trip_distance < 1 THEN '< 1 mile'
        WHEN trip_distance < 3 THEN '1-3 miles'
        WHEN trip_distance < 5 THEN '3-5 miles'
        WHEN trip_distance < 10 THEN '5-10 miles'
        WHEN trip_distance < 20 THEN '10-20 miles'
        ELSE '20+ miles'
    END as distance_range,
    COUNT(*) as trip_count,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
GROUP BY distance_range
ORDER BY MIN(trip_distance);

-- Average trip duration by hour
SELECT
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count,
    ROUND(AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60)::numeric, 2) as avg_duration_minutes,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance
FROM rides
WHERE dropoff_datetime > pickup_datetime
GROUP BY hour
ORDER BY hour;

-- ====================
-- 4. PASSENGER ANALYSIS
-- ====================

-- Passenger count distribution
SELECT
    passenger_count,
    COUNT(*) as trip_count,
    ROUND(AVG(trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM rides
WHERE passenger_count > 0
GROUP BY passenger_count
ORDER BY passenger_count;

-- ====================
-- 5. LOCATION ANALYSIS
-- ====================

-- Top 10 pickup locations
SELECT
    z.borough,
    z.zone,
    COUNT(*) as pickup_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare
FROM rides r
LEFT JOIN zones z ON r.pickup_location_id = z.location_id
WHERE z.zone IS NOT NULL
GROUP BY z.borough, z.zone
ORDER BY pickup_count DESC
LIMIT 10;

-- Top 10 dropoff locations
SELECT
    z.borough,
    z.zone,
    COUNT(*) as dropoff_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare
FROM rides r
LEFT JOIN zones z ON r.dropoff_location_id = z.location_id
WHERE z.zone IS NOT NULL
GROUP BY z.borough, z.zone
ORDER BY dropoff_count DESC
LIMIT 10;

-- Popular routes (top 10 pickup-dropoff pairs)
SELECT
    z_pickup.zone as pickup_zone,
    z_dropoff.zone as dropoff_zone,
    COUNT(*) as trip_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare
FROM rides r
LEFT JOIN zones z_pickup ON r.pickup_location_id = z_pickup.location_id
LEFT JOIN zones z_dropoff ON r.dropoff_location_id = z_dropoff.location_id
WHERE z_pickup.zone IS NOT NULL AND z_dropoff.zone IS NOT NULL
GROUP BY z_pickup.zone, z_dropoff.zone
ORDER BY trip_count DESC
LIMIT 10;

-- ====================
-- 6. TIP ANALYSIS
-- ====================

-- Tip statistics (credit card payments only show tips)
SELECT
    COUNT(*) as trips_with_tips,
    ROUND(AVG(tip_amount)::numeric, 2) as avg_tip,
    ROUND(MIN(tip_amount)::numeric, 2) as min_tip,
    ROUND(MAX(tip_amount)::numeric, 2) as max_tip,
    ROUND(AVG(tip_amount / NULLIF(fare_amount, 0) * 100)::numeric, 2) as avg_tip_percentage
FROM rides
WHERE payment_type = 1  -- Credit card only
AND tip_amount > 0;

-- Tip distribution by fare amount
SELECT
    CASE
        WHEN fare_amount < 10 THEN '< $10'
        WHEN fare_amount < 20 THEN '$10-20'
        WHEN fare_amount < 30 THEN '$20-30'
        WHEN fare_amount < 50 THEN '$30-50'
        ELSE '$50+'
    END as fare_range,
    COUNT(*) as trip_count,
    ROUND(AVG(tip_amount)::numeric, 2) as avg_tip,
    ROUND(AVG(tip_amount / NULLIF(fare_amount, 0) * 100)::numeric, 2) as avg_tip_pct
FROM rides
WHERE payment_type = 1 AND tip_amount > 0
GROUP BY fare_range
ORDER BY MIN(fare_amount);
