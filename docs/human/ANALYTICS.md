# Analytics Guide

## 📊 Basic Analytics Queries

### 1. Trip Volume Analysis

#### Total Trips

```sql
SELECT COUNT(*) as total_trips
FROM rides;
```

#### Trips by Vendor

```sql
SELECT
    v.vendor_name,
    COUNT(*) as trip_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM rides r
JOIN vendors v ON r.vendor_id = v.vendor_id
GROUP BY v.vendor_name
ORDER BY trip_count DESC;
```

#### Trips by Hour of Day

```sql
SELECT
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count,
    AVG(total_amount) as avg_fare
FROM rides
GROUP BY hour
ORDER BY hour;
```

#### Trips by Day of Week

```sql
SELECT
    TO_CHAR(pickup_datetime, 'Day') as day_name,
    EXTRACT(DOW FROM pickup_datetime) as day_num,
    COUNT(*) as trip_count,
    AVG(trip_distance) as avg_distance,
    AVG(total_amount) as avg_fare
FROM rides
GROUP BY day_name, day_num
ORDER BY day_num;
```

### 2. Financial Analysis

#### Revenue Summary

```sql
SELECT
    COUNT(*) as total_trips,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_fare,
    MIN(total_amount) as min_fare,
    MAX(total_amount) as max_fare,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_amount) as median_fare
FROM rides
WHERE total_amount > 0;
```

#### Revenue by Payment Type

```sql
SELECT
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Unknown'
    END as payment_method,
    COUNT(*) as trip_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_fare,
    AVG(tip_amount) as avg_tip
FROM rides
GROUP BY payment_type
ORDER BY total_revenue DESC;
```

#### Daily Revenue Trend

```sql
SELECT
    DATE(pickup_datetime) as date,
    COUNT(*) as trips,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_fare,
    SUM(tip_amount) as total_tips
FROM rides
GROUP BY date
ORDER BY date;
```

### 3. Distance and Duration Analysis

#### Trip Distance Distribution

```sql
SELECT
    CASE
        WHEN trip_distance <= 1 THEN '0-1 miles'
        WHEN trip_distance <= 3 THEN '1-3 miles'
        WHEN trip_distance <= 5 THEN '3-5 miles'
        WHEN trip_distance <= 10 THEN '5-10 miles'
        ELSE '10+ miles'
    END as distance_range,
    COUNT(*) as trip_count,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance
FROM rides
GROUP BY distance_range
ORDER BY MIN(trip_distance);
```

#### Average Speed Analysis

```sql
SELECT
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trips,
    AVG(trip_distance) as avg_distance,
    AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60) as avg_duration_minutes,
    AVG(trip_distance / NULLIF(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))
    /3600, 0))
    as avg_speed_mph
FROM rides
WHERE trip_distance > 0
  AND dropoff_datetime > pickup_datetime
GROUP BY hour
ORDER BY hour;
```

#### Trip Duration Distribution

```sql
SELECT
    CASE
        WHEN EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60 <= 10
        THEN '0-10 min'
        WHEN EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60 <= 20
        THEN '10-20 min'
        WHEN EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60 <= 30
        THEN '20-30 min'
        WHEN EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60 <= 60
        THEN '30-60 min'
        ELSE '60+ min'
    END as duration_range,
    COUNT(*) as trip_count,
    AVG(trip_distance) as avg_distance,
    AVG(total_amount) as avg_fare
FROM rides
WHERE dropoff_datetime > pickup_datetime
GROUP BY duration_range
ORDER BY MIN(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60);
```

### 4. Passenger Analysis

#### Passenger Count Distribution

```sql
SELECT
    passenger_count,
    COUNT(*) as trip_count,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM rides
WHERE passenger_count > 0
GROUP BY passenger_count
ORDER BY passenger_count;
```

#### Solo vs Group Rides

```sql
SELECT
    CASE
        WHEN passenger_count = 1 THEN 'Solo'
        ELSE 'Group'
    END as ride_type,
    COUNT(*) as trip_count,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance,
    AVG(tip_amount) as avg_tip
FROM rides
WHERE passenger_count > 0
GROUP BY ride_type;
```

### 5. Location Analysis

#### Top Pickup Locations

```sql
SELECT
    pickup_location_id,
    COUNT(*) as pickup_count,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance
FROM rides
GROUP BY pickup_location_id
ORDER BY pickup_count DESC
LIMIT 20;
```

#### Top Dropoff Locations

```sql
SELECT
    dropoff_location_id,
    COUNT(*) as dropoff_count,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance
FROM rides
GROUP BY dropoff_location_id
ORDER BY dropoff_count DESC
LIMIT 20;
```

#### Popular Routes

```sql
SELECT
    pickup_location_id,
    dropoff_location_id,
    COUNT(*) as trip_count,
    AVG(trip_distance) as avg_distance,
    AVG(total_amount) as avg_fare,
    AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60) as avg_duration_min
FROM rides
WHERE pickup_location_id != dropoff_location_id
GROUP BY pickup_location_id, dropoff_location_id
HAVING COUNT(*) > 10
ORDER BY trip_count DESC
LIMIT 30;
```

## 🚀 Advanced Analytics Queries

### 1. Window Functions

#### Running Total Revenue

```sql
SELECT
    DATE(pickup_datetime) as date,
    SUM(total_amount) as daily_revenue,
    SUM(SUM(total_amount)) OVER (ORDER BY DATE(pickup_datetime)) as running_total
FROM rides
GROUP BY date
ORDER BY date;
```

#### Ranking Vendors by Performance

```sql
WITH vendor_metrics AS (
    SELECT
        v.vendor_name,
        DATE(r.pickup_datetime) as date,
        COUNT(*) as trips,
        SUM(r.total_amount) as revenue,
        AVG(r.total_amount) as avg_fare
    FROM rides r
    JOIN vendors v ON r.vendor_id = v.vendor_id
    GROUP BY v.vendor_name, date
)
SELECT
    vendor_name,
    date,
    trips,
    revenue,
    RANK() OVER (PARTITION BY date ORDER BY revenue DESC) as revenue_rank,
    RANK() OVER (PARTITION BY date ORDER BY trips DESC) as trips_rank
FROM vendor_metrics
ORDER BY date DESC, revenue DESC;
```

#### Moving Average (7-day)

```sql
WITH daily_stats AS (
    SELECT
        DATE(pickup_datetime) as date,
        COUNT(*) as trips,
        SUM(total_amount) as revenue,
        AVG(total_amount) as avg_fare
    FROM rides
    GROUP BY date
)
SELECT
    date,
    trips,
    revenue,
    AVG(revenue) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7day,
    AVG(trips) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_trips_7day
FROM daily_stats
ORDER BY date;
```

### 2. Common Table Expressions (CTEs)

#### Hourly Peak Analysis

```sql
WITH hourly_stats AS (
    SELECT
        EXTRACT(HOUR FROM pickup_datetime) as hour,
        DATE(pickup_datetime) as date,
        COUNT(*) as trips,
        SUM(total_amount) as revenue
    FROM rides
    GROUP BY hour, date
),
hourly_avg AS (
    SELECT
        hour,
        AVG(trips) as avg_trips,
        STDDEV(trips) as stddev_trips
    FROM hourly_stats
    GROUP BY hour
)
SELECT
    h.hour,
    h.avg_trips,
    h.stddev_trips,
    CASE
        WHEN h.avg_trips > (SELECT AVG(avg_trips) FROM hourly_avg) + (SELECT AVG(stddev_trips) FROM hourly_avg)
        THEN 'Peak Hour'
        WHEN h.avg_trips < (SELECT AVG(avg_trips) FROM hourly_avg) - (SELECT AVG(stddev_trips) FROM hourly_avg)
        THEN 'Off-Peak'
        ELSE 'Normal'
    END as hour_classification
FROM hourly_avg h
ORDER BY h.hour;
```

#### Cohort Analysis by Date

```sql
WITH first_week AS (
    SELECT
        DATE_TRUNC('week', MIN(pickup_datetime)) as cohort_week
    FROM rides
),
weekly_stats AS (
    SELECT
        DATE_TRUNC('week', pickup_datetime) as week,
        COUNT(*) as trips,
        SUM(total_amount) as revenue
    FROM rides
    GROUP BY week
)
SELECT
    week,
    trips,
    revenue,
    trips - LAG(trips) OVER (ORDER BY week) as trip_change,
    ROUND(
        ((trips - LAG(trips) OVER (ORDER BY week))::NUMERIC /
         NULLIF(LAG(trips) OVER (ORDER BY week), 0)) * 100,
        2
    ) as trip_change_pct
FROM weekly_stats
ORDER BY week;
```

### 3. Statistical Analysis

#### Fare Percentiles

```sql
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_amount) as q1,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_amount) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_amount) as q3,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY total_amount) as p90,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_amount) as p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_amount) as p99
FROM rides
WHERE total_amount > 0;
```

#### Correlation Between Distance and Fare

```sql
WITH trip_stats AS (
    SELECT
        trip_distance,
        total_amount,
        AVG(total_amount) OVER () as avg_amount,
        AVG(trip_distance) OVER () as avg_distance
    FROM rides
    WHERE trip_distance > 0 AND total_amount > 0
)
SELECT
    CORR(trip_distance, total_amount) as correlation,
    REGR_SLOPE(total_amount, trip_distance) as fare_per_mile,
    REGR_INTERCEPT(total_amount, trip_distance) as base_fare
FROM trip_stats;
```

### 4. Time Series Analysis

#### Hourly Patterns by Day of Week

```sql
SELECT
    TO_CHAR(pickup_datetime, 'Day') as day_name,
    EXTRACT(DOW FROM pickup_datetime) as day_num,
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trips,
    AVG(total_amount) as avg_fare,
    SUM(total_amount) as revenue
FROM rides
GROUP BY day_name, day_num, hour
ORDER BY day_num, hour;
```

#### Week-over-Week Growth

```sql
WITH weekly_stats AS (
    SELECT
        DATE_TRUNC('week', pickup_datetime) as week,
        COUNT(*) as trips,
        SUM(total_amount) as revenue
    FROM rides
    GROUP BY week
)
SELECT
    week,
    trips,
    revenue,
    LAG(trips, 1) OVER (ORDER BY week) as prev_week_trips,
    LAG(revenue, 1) OVER (ORDER BY week) as prev_week_revenue,
    ROUND(
        ((trips - LAG(trips, 1) OVER (ORDER BY week))::NUMERIC /
         NULLIF(LAG(trips, 1) OVER (ORDER BY week), 0)) * 100,
        2
    ) as trip_growth_pct,
    ROUND(
        ((revenue - LAG(revenue, 1) OVER (ORDER BY week))::NUMERIC /
         NULLIF(LAG(revenue, 1) OVER (ORDER BY week), 0)) * 100,
        2
    ) as revenue_growth_pct
FROM weekly_stats
ORDER BY week;
```

## 📈 Key Performance Indicators (KPIs)

### Daily Dashboard Query

```sql
WITH today_stats AS (
    SELECT
        COUNT(*) as trips_today,
        SUM(total_amount) as revenue_today,
        AVG(total_amount) as avg_fare_today,
        AVG(trip_distance) as avg_distance_today
    FROM rides
    WHERE DATE(pickup_datetime) = CURRENT_DATE
),
yesterday_stats AS (
    SELECT
        COUNT(*) as trips_yesterday,
        SUM(total_amount) as revenue_yesterday
    FROM rides
    WHERE DATE(pickup_datetime) = CURRENT_DATE - 1
)
SELECT
    t.trips_today,
    t.revenue_today,
    t.avg_fare_today,
    t.avg_distance_today,
    ROUND((t.trips_today - y.trips_yesterday)::NUMERIC
           / NULLIF(y.trips_yesterday, 0) * 100, 2)
           as trip_change_pct,
    ROUND((t.revenue_today - y.revenue_yesterday)::NUMERIC
           / NULLIF(y.revenue_yesterday, 0) * 100, 2)
           as revenue_change_pct
FROM today_stats t
CROSS JOIN yesterday_stats y;
```

### Monthly Summary

```sql
SELECT
    DATE_TRUNC('month', pickup_datetime) as month,
    COUNT(*) as total_trips,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance,
    SUM(tip_amount) as total_tips,
    COUNT(DISTINCT DATE(pickup_datetime)) as active_days
FROM rides
GROUP BY month
ORDER BY month DESC;
```

---

**Last Updated:** November 2, 2025
