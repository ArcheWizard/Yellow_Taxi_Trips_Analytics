# Database Schema Reference - AI Assistant

## 🗄️ Quick Reference

This is a concise, AI-optimized reference for the database schema. Use this when writing queries or understanding table relationships.

## 📊 Tables

### `vendors`

**Purpose:** Lookup table for taxi vendors/companies

| Column      | Type         | Constraints | Description              |
| ----------- | ------------ | ----------- | ------------------------ |
| vendor_id   | INTEGER      | PK          | Unique vendor identifier |
| vendor_name | VARCHAR(100) | -           | Company name             |

**Data:**

- 1 = Creative Mobile Technologies
- 2 = VeriFone Inc.

**Common Joins:**

```sql
FROM rides r
JOIN vendors v ON r.vendor_id = v.vendor_id
```

---

### `zones`

**Purpose:** NYC taxi zone lookup table

| Column       | Type         | Constraints | Description            |
| ------------ | ------------ | ----------- | ---------------------- |
| location_id  | INTEGER      | PK          | Unique zone identifier |
| borough      | VARCHAR(50)  | -           | NYC borough            |
| zone         | VARCHAR(100) | -           | Zone name              |
| service_zone | VARCHAR(50)  | -           | Service classification |

**Values:**

- borough: Manhattan, Brooklyn, Queens, Bronx, Staten Island, EWR, Unknown
- service_zone: Yellow Zone, Boro Zone, Airports

**Common Joins:**

```sql
FROM rides r
LEFT JOIN zones z_pickup ON r.pickup_location_id = z_pickup.location_id
LEFT JOIN zones z_dropoff ON r.dropoff_location_id = z_dropoff.location_id
```

**Note:** Use LEFT JOIN because some rides have NULL location_id

---

### `rides` (Fact Table)

**Purpose:** Main transactional table for taxi trips

#### Identity & References

| Column    | Type      | Constraints  | Description       |
| --------- | --------- | ------------ | ----------------- |
| ride_id   | BIGSERIAL | PK           | Auto-generated ID |
| vendor_id | INTEGER   | FK → vendors | Vendor reference  |

#### Timestamps

| Column           | Type      | Constraints   | Description                |
| ---------------- | --------- | ------------- | -------------------------- |
| pickup_datetime  | TIMESTAMP | NOT NULL      | When passenger picked up   |
| dropoff_datetime | TIMESTAMP | NOT NULL      | When passenger dropped off |
| created_at       | TIMESTAMP | DEFAULT NOW() | Record insertion time      |

#### Trip Details

| Column              | Type         | Constraints | Description                |
| ------------------- | ------------ | ----------- | -------------------------- |
| passenger_count     | INTEGER      | -           | Number of passengers (1-6) |
| trip_distance       | NUMERIC(8,2) | -           | Distance in miles          |
| pickup_location_id  | INTEGER      | FK → zones  | Pickup zone                |
| dropoff_location_id | INTEGER      | FK → zones  | Dropoff zone               |

#### Rate & Payment

| Column             | Type    | Constraints | Description            |
| ------------------ | ------- | ----------- | ---------------------- |
| rate_code_id       | INTEGER | -           | Rate type (1-6)        |
| store_and_fwd_flag | CHAR(1) | -           | Y=stored, N=not stored |
| payment_type       | INTEGER | -           | Payment method (1-6)   |

**rate_code_id Values:**

1. Standard rate
2. JFK
3. Newark
4. Nassau or Westchester
5. Negotiated fare
6. Group ride

**payment_type Values:**

1. Credit card
2. Cash
3. No charge
4. Dispute
5. Unknown
6. Voided trip

#### Financial Fields

| Column                | Type         | Constraints | Description                 |
| --------------------- | ------------ | ----------- | --------------------------- |
| fare_amount           | NUMERIC(8,2) | -           | Base fare                   |
| extra                 | NUMERIC(8,2) | -           | Extra charges               |
| mta_tax               | NUMERIC(8,2) | -           | MTA tax ($0.50)             |
| tip_amount            | NUMERIC(8,2) | -           | Tip (credit card only)      |
| tolls_amount          | NUMERIC(8,2) | -           | Total tolls                 |
| improvement_surcharge | NUMERIC(8,2) | -           | Improvement ($0.30)         |
| total_amount          | NUMERIC(8,2) | -           | Total charged               |
| congestion_surcharge  | NUMERIC(8,2) | -           | Congestion surcharge        |
| airport_fee           | NUMERIC(8,2) | -           | Airport fee ($1.25 JFK/LGA) |

**Important Notes:**

- `tip_amount` is 0 for cash payments (not recorded)
- `total_amount` = fare + extra + mta_tax + tip + tolls + surcharges
- All amounts in USD

---

## 🔍 Indexes

### Single Column Indexes

```sql
idx_rides_pickup_datetime    ON rides(pickup_datetime)
idx_rides_dropoff_datetime   ON rides(dropoff_datetime)
idx_rides_pickup_location    ON rides(pickup_location_id)
idx_rides_dropoff_location   ON rides(dropoff_location_id)
idx_rides_vendor             ON rides(vendor_id)
```

### Composite Indexes

```sql
idx_rides_datetime_location  ON rides(pickup_datetime, pickup_location_id)
```

### When to Use Each Index

**Use pickup_datetime index:**

- Time-based filtering: `WHERE pickup_datetime >= '2024-11-01'`
- Time-based grouping: `GROUP BY DATE(pickup_datetime)`
- Time-based ordering: `ORDER BY pickup_datetime`

**Use pickup_location index:**

- Location filtering: `WHERE pickup_location_id = 161`
- Location grouping: `GROUP BY pickup_location_id`

**Use composite index:**

- Combined filters: `WHERE pickup_datetime >= '2024-11-01' AND pickup_location_id = 161`

**Use vendor index:**

- Vendor filtering: `WHERE vendor_id = 1`
- Joins with vendors table: `JOIN vendors v ON r.vendor_id = v.vendor_id`

---

## 📝 Query Patterns

### Basic Aggregation

```sql
-- Count by vendor
SELECT
    v.vendor_name,
    COUNT(*) as trips
FROM rides r
JOIN vendors v ON r.vendor_id = v.vendor_id
GROUP BY v.vendor_name;
```

### Time-based Analysis

```sql
-- Hourly pattern
SELECT
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trips,
    AVG(total_amount) as avg_fare
FROM rides
WHERE pickup_datetime >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour;
```

### Location Analysis

```sql
-- Top pickup zones
SELECT
    z.zone,
    z.borough,
    COUNT(*) as pickup_count
FROM rides r
LEFT JOIN zones z ON r.pickup_location_id = z.location_id
GROUP BY z.zone, z.borough
ORDER BY pickup_count DESC
LIMIT 10;
```

### Revenue Analysis

```sql
-- Daily revenue
SELECT
    DATE(pickup_datetime) as date,
    COUNT(*) as trips,
    SUM(total_amount) as revenue,
    AVG(total_amount) as avg_fare
FROM rides
WHERE pickup_datetime >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date
ORDER BY date;
```

### Window Functions

```sql
-- Running total
SELECT
    DATE(pickup_datetime) as date,
    SUM(total_amount) as daily_revenue,
    SUM(SUM(total_amount)) OVER (ORDER BY DATE(pickup_datetime)) as running_total
FROM rides
GROUP BY date
ORDER BY date;
```

### CTEs for Complex Queries

```sql
WITH daily_stats AS (
    SELECT
        DATE(pickup_datetime) as date,
        COUNT(*) as trips,
        AVG(total_amount) as avg_fare
    FROM rides
    GROUP BY date
)
SELECT
    date,
    trips,
    avg_fare,
    trips - LAG(trips) OVER (ORDER BY date) as trip_change
FROM daily_stats
ORDER BY date;
```

---

## 🎯 Common Filters

### Date Ranges

```sql
-- Specific date
WHERE DATE(pickup_datetime) = '2024-11-01'

-- Date range (better for indexes)
WHERE pickup_datetime >= '2024-11-01'
  AND pickup_datetime < '2024-11-02'

-- Last 7 days
WHERE pickup_datetime >= CURRENT_DATE - INTERVAL '7 days'

-- Current month
WHERE pickup_datetime >= DATE_TRUNC('month', CURRENT_DATE)
```

### Valid Data Filters

```sql
-- Valid trips only
WHERE fare_amount > 0
  AND trip_distance > 0
  AND passenger_count > 0
  AND pickup_datetime < dropoff_datetime
```

### Payment Type Filters

```sql
-- Credit card payments (have tips)
WHERE payment_type = 1

-- Cash payments (no tip data)
WHERE payment_type = 2

-- Paid trips only
WHERE payment_type IN (1, 2)
```

---

## ⚡ Performance Tips

### DO's

✅ **Use date ranges instead of DATE() function:**

```sql
-- Good (uses index)
WHERE pickup_datetime >= '2024-11-01'
  AND pickup_datetime < '2024-11-02'

-- Bad (can't use index)
WHERE DATE(pickup_datetime) = '2024-11-01'
```

✅ **Use indexed columns in WHERE:**

```sql
-- Good
WHERE pickup_datetime >= '2024-11-01'

-- Less optimal
WHERE dropoff_datetime >= '2024-11-01'
```

✅ **Use LIMIT for exploratory queries:**

```sql
-- Good for testing
SELECT * FROM rides LIMIT 100

-- Bad for testing
SELECT * FROM rides
```

✅ **Use specific columns:**

```sql
-- Good
SELECT ride_id, total_amount FROM rides

-- Bad
SELECT * FROM rides
```

### DON'Ts

❌ **Avoid functions on indexed columns:**

```sql
-- Bad
WHERE EXTRACT(HOUR FROM pickup_datetime) = 8

-- Better
WHERE pickup_datetime >= '2024-11-01 08:00:00'
  AND pickup_datetime < '2024-11-01 09:00:00'
```

❌ **Avoid OR conditions on different columns:**

```sql
-- Bad
WHERE pickup_location_id = 161 OR dropoff_location_id = 161

-- Better (use UNION)
SELECT * FROM rides WHERE pickup_location_id = 161
UNION
SELECT * FROM rides WHERE dropoff_location_id = 161
```

---

## 🔢 Common Calculations

### Trip Duration

```sql
EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime)) / 60 AS duration_minutes
```

### Average Speed

```sql
trip_distance / NULLIF(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime)) / 3600, 0) AS speed_mph
```

### Revenue Per Mile

```sql
total_amount / NULLIF(trip_distance, 0) AS revenue_per_mile
```

### Tip Percentage (Credit Cards)

```sql
CASE
    WHEN payment_type = 1 AND fare_amount > 0
    THEN (tip_amount / fare_amount) * 100
    ELSE NULL
END AS tip_percentage
```

---

## 📊 Sample Row

```text
ride_id: 1
vendor_id: 2
pickup_datetime: 2024-11-01 08:30:00
dropoff_datetime: 2024-11-01 08:45:00
passenger_count: 1
trip_distance: 2.50
pickup_location_id: 161
dropoff_location_id: 234
rate_code_id: 1
store_and_fwd_flag: N
payment_type: 1
fare_amount: 12.50
extra: 0.50
mta_tax: 0.50
tip_amount: 2.50
tolls_amount: 0.00
improvement_surcharge: 0.30
total_amount: 16.30
congestion_surcharge: 2.50
airport_fee: 0.00
created_at: 2024-11-02 10:00:00
```

---

**Last Updated:** November 2, 2025
