# Database Documentation

## 📊 Database Schema

### Overview

The database is designed following a star schema pattern with a central fact table (`rides`) and dimension tables (`zones`, `vendors`).

### Entity Relationship Diagram

```text
┌─────────────┐
│   vendors   │
│             │
│ vendor_id PK│─────┐
│ vendor_name │     │
└─────────────┘     │
                    │
                    │ FK
                    ▼
┌─────────────────────────────────┐
│           rides                 │
│                                 │
│ ride_id PK                      │
│ vendor_id FK                    │──┐
│ pickup_datetime                 │  │
│ dropoff_datetime                │  │
│ passenger_count                 │  │
│ trip_distance                   │  │
│ pickup_location_id FK           │──┼───┐
│ dropoff_location_id FK          │──┼───┤
│ rate_code_id                    │  │   │
│ store_and_fwd_flag              │  │   │
│ payment_type                    │  │   │
│ fare_amount                     │  │   │
│ extra                           │  │   │
│ mta_tax                         │  │   │
│ tip_amount                      │  │   │
│ tolls_amount                    │  │   │
│ improvement_surcharge           │  │   │
│ total_amount                    │  │   │
│ congestion_surcharge            │  │   │
│ airport_fee                     │  │   │
│ created_at                      │  │   │
└─────────────────────────────────┘  │   │
                                     │   │
                    ┌────────────────┘   │
                    │                    │
                    ▼                    ▼
              ┌─────────────┐      ┌─────────────┐
              │    zones    │      │    zones    │
              │             │      │             │
              │location_id PK│      │location_id PK│
              │ borough     │      │ borough     │
              │ zone        │      │ zone        │
              │service_zone │      │service_zone │
              └─────────────┘      └─────────────┘
                  (pickup)           (dropoff)
```

## 📋 Table Definitions

### 1. `vendors` Table

Stores taxi vendor/company information.

```sql
CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY,
    vendor_name VARCHAR(100)
);
```

**Columns:**

- `vendor_id` (PK): Unique identifier for the vendor
  - 1 = Creative Mobile Technologies
  - 2 = VeriFone Inc.
- `vendor_name`: Name of the vendor company

**Sample Data:**

```sql
SELECT * FROM vendors;
```

| vendor_id | vendor_name                   |
|-----------|-------------------------------|
| 1         | Creative Mobile Technologies  |
| 2         | VeriFone Inc.                 |

### 2. `zones` Table

Stores NYC taxi zone information for pickup and dropoff locations.

```sql
CREATE TABLE zones (
    location_id INTEGER PRIMARY KEY,
    borough VARCHAR(50),
    zone VARCHAR(100),
    service_zone VARCHAR(50)
);
```

**Columns:**

- `location_id` (PK): Unique identifier for the zone
- `borough`: NYC borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
- `zone`: Specific zone name (e.g., "JFK Airport", "Times Square")
- `service_zone`: Service classification (Yellow Zone, Green Zone, etc.)

**Notes:**

- This table should be populated from NYC TLC zone lookup data
- Download from: <https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv>

### 3. `rides` Table (Fact Table)

Stores individual taxi trip records.

```sql
CREATE TABLE rides (
    ride_id BIGSERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    pickup_datetime TIMESTAMP NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count INTEGER,
    trip_distance NUMERIC(8,2),
    pickup_location_id INTEGER REFERENCES zones(location_id),
    dropoff_location_id INTEGER REFERENCES zones(location_id),
    rate_code_id INTEGER,
    store_and_fwd_flag CHAR(1),
    payment_type INTEGER,
    fare_amount NUMERIC(8,2),
    extra NUMERIC(8,2),
    mta_tax NUMERIC(8,2),
    tip_amount NUMERIC(8,2),
    tolls_amount NUMERIC(8,2),
    improvement_surcharge NUMERIC(8,2),
    total_amount NUMERIC(8,2),
    congestion_surcharge NUMERIC(8,2),
    airport_fee NUMERIC(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**

**Identity & References:**

- `ride_id` (PK): Auto-generated unique identifier
- `vendor_id` (FK): Reference to vendors table

**Datetime:**

- `pickup_datetime`: When passenger was picked up
- `dropoff_datetime`: When passenger was dropped off
- `created_at`: Record insertion timestamp

**Trip Details:**

- `passenger_count`: Number of passengers (1-6)
- `trip_distance`: Distance in miles
- `pickup_location_id` (FK): Pickup zone
- `dropoff_location_id` (FK): Dropoff zone

**Rate Information:**

- `rate_code_id`: Rate type applied
  - 1 = Standard rate
  - 2 = JFK
  - 3 = Newark
  - 4 = Nassau or Westchester
  - 5 = Negotiated fare
  - 6 = Group ride
- `store_and_fwd_flag`: Whether trip was stored before sending to vendor
  - Y = Store and forward
  - N = Not stored

**Payment:**

- `payment_type`: How passenger paid
  - 1 = Credit card
  - 2 = Cash
  - 3 = No charge
  - 4 = Dispute
  - 5 = Unknown
  - 6 = Voided trip

**Financial:**

- `fare_amount`: Base time-and-distance fare
- `extra`: Extra charges (rush hour, overnight)
- `mta_tax`: MTA tax ($0.50)
- `tip_amount`: Tip (credit card only)
- `tolls_amount`: Total tolls paid
- `improvement_surcharge`: Improvement surcharge ($0.30)
- `congestion_surcharge`: Congestion surcharge
- `airport_fee`: Airport fee ($1.25 for JFK/LaGuardia)
- `total_amount`: Total amount charged to passenger

## 🔍 Indexes

Indexes are crucial for query performance.

```sql
-- Single column indexes
CREATE INDEX idx_rides_pickup_datetime ON rides(pickup_datetime);
CREATE INDEX idx_rides_dropoff_datetime ON rides(dropoff_datetime);
CREATE INDEX idx_rides_pickup_location ON rides(pickup_location_id);
CREATE INDEX idx_rides_dropoff_location ON rides(dropoff_location_id);
CREATE INDEX idx_rides_vendor ON rides(vendor_id);

-- Composite index for common query patterns
CREATE INDEX idx_rides_datetime_location ON rides(pickup_datetime, pickup_location_id);
```

**Index Usage Guidelines:**

- `idx_rides_pickup_datetime`: Time-based queries (peak hours, trends)
- `idx_rides_pickup_location`: Location-based queries (popular zones)
- `idx_rides_datetime_location`: Combined time and location queries
- `idx_rides_vendor`: Vendor performance analysis

**Check Index Usage:**

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

## 📊 Data Statistics

### Get Table Sizes

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Get Row Counts

```sql
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

## 🔧 Maintenance Operations

### Update Statistics

```sql
-- Analyze all tables
ANALYZE;

-- Analyze specific table
ANALYZE rides;

-- Verbose output
ANALYZE VERBOSE rides;
```

### Vacuum Operations

```sql
-- Regular vacuum
VACUUM rides;

-- Full vacuum (locks table)
VACUUM FULL rides;

-- Vacuum and analyze
VACUUM ANALYZE rides;
```

### Reindex

```sql
-- Reindex table
REINDEX TABLE rides;

-- Reindex specific index
REINDEX INDEX idx_rides_pickup_datetime;
```

## 📈 Performance Monitoring

### Check Query Performance

```sql
-- Enable query timing
\timing

-- Show query plan
EXPLAIN SELECT * FROM rides WHERE pickup_datetime > '2024-11-01';

-- Show query plan with execution
EXPLAIN ANALYZE SELECT * FROM rides WHERE pickup_datetime > '2024-11-01';
```

### Slow Query Log

Edit `postgresql.conf`:

```ini
log_min_duration_statement = 1000  # Log queries taking > 1 second
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'all'
```

### Check Active Connections

```sql
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE datname = 'city_rides_db'
  AND state != 'idle'
ORDER BY query_start;
```

## 🔐 Security & Permissions

### Grant Read-Only Access

```sql
-- Create read-only role
CREATE ROLE readonly;

-- Grant connect privilege
GRANT CONNECT ON DATABASE city_rides_db TO readonly;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO readonly;

-- Grant select on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- Create read-only user
CREATE USER analyst_user WITH PASSWORD 'analyst_password';
GRANT readonly TO analyst_user;
```

### Grant Write Access

```sql
-- Grant insert, update, delete
GRANT INSERT, UPDATE, DELETE ON rides TO rides_user;

-- Grant usage on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rides_user;
```

## 💾 Backup & Restore

### Backup Database

```bash
# Full database backup
pg_dump -U rides_user -d city_rides_db -F c -f city_rides_backup.dump

# Schema only
pg_dump -U rides_user -d city_rides_db -s -f schema_backup.sql

# Data only
pg_dump -U rides_user -d city_rides_db -a -f data_backup.sql

# Specific table
pg_dump -U rides_user -d city_rides_db -t rides -F c -f rides_backup.dump
```

### Restore Database

```bash
# Restore custom format
pg_restore -U rides_user -d city_rides_db -c city_rides_backup.dump

# Restore SQL format
psql -U rides_user -d city_rides_db -f schema_backup.sql
```

## 🧪 Testing Queries

### Verify Data Integrity

```sql
-- Check for null values in required fields
SELECT COUNT(*) as null_count
FROM rides
WHERE pickup_datetime IS NULL
   OR dropoff_datetime IS NULL
   OR vendor_id IS NULL;

-- Check for invalid trip distances
SELECT COUNT(*) as invalid_distance
FROM rides
WHERE trip_distance <= 0 OR trip_distance > 100;

-- Check for invalid passenger counts
SELECT COUNT(*) as invalid_passengers
FROM rides
WHERE passenger_count <= 0 OR passenger_count > 10;

-- Check for invalid timestamps
SELECT COUNT(*) as invalid_timestamps
FROM rides
WHERE pickup_datetime >= dropoff_datetime;

-- Check for invalid fares
SELECT COUNT(*) as invalid_fares
FROM rides
WHERE total_amount <= 0 OR fare_amount < 0;
```

### Data Quality Report

```sql
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT vendor_id) as unique_vendors,
    MIN(pickup_datetime) as earliest_trip,
    MAX(pickup_datetime) as latest_trip,
    AVG(trip_distance) as avg_distance,
    AVG(total_amount) as avg_fare,
    SUM(CASE WHEN payment_type = 1 THEN 1 ELSE 0 END) as credit_card_payments,
    SUM(CASE WHEN payment_type = 2 THEN 1 ELSE 0 END) as cash_payments
FROM rides;
```

---

**Last Updated:** November 2, 2025
