# Step-by-Step Implementation Guide

## 📋 Overview

This is the comprehensive step-by-step guide from the original project specification. Follow these steps in order to complete the City Rides Analytics Dashboard project.

**Current Status:** Phase 1 - Foundation (In Progress)

---

## 🚀 PHASE 1: Foundation & Setup

### Step 1: Environment Setup ✅

**Goal:** Install all required software and create project structure

**Tasks:**

1. Install PostgreSQL 14+
2. Install Python 3.9+
3. Create virtual environment
4. Install Python dependencies
5. Create project directory structure

**Commands:**

```bash
# Install PostgreSQL
sudo apt update && sudo apt install postgresql postgresql-contrib

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install psycopg2-binary pandas pyarrow python-dotenv sqlalchemy fastapi uvicorn
pip freeze > requirements.txt
```

**Verification:**

- [ ] PostgreSQL running: `sudo systemctl status postgresql`
- [ ] Python 3.9+: `python --version`
- [ ] Virtual env activated: Check prompt shows `(venv)`
- [ ] Dependencies installed: `pip list`

**Documentation:** See `docs/human/SETUP.md`

---

### Step 2: Database Creation ✅

**Goal:** Create PostgreSQL database and user

**Tasks:**

1. Create database: `city_rides_db`
2. Create user: `rides_user` with password
3. Grant necessary privileges
4. Test connection

**Commands:**

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE city_rides_db;
CREATE USER rides_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE city_rides_db TO rides_user;
\c city_rides_db
GRANT ALL ON SCHEMA public TO rides_user;
\q
```

**Verification:**

- [ ] Database exists: `psql -U rides_user -d city_rides_db -c "\l"`
- [ ] Can connect: `psql -U rides_user -d city_rides_db`

---

### Step 3: Schema Design & Implementation ⏳

**Goal:** Create tables with proper structure, foreign keys, and indexes

**Files to Create:**

- `sql/schema.sql` - Main schema definition

**Tasks:**

1. Create vendors table
2. Create zones table (structure ready, data to be loaded later)
3. Create rides fact table
4. Add foreign key constraints
5. Create B-tree indexes on frequently queried columns
6. Add comments for documentation

**Apply Schema:**

```bash
psql -U rides_user -d city_rides_db -f sql/schema.sql
```

**Verification:**

- [ ] Tables created: `\dt`
- [ ] Indexes created: `\di`
- [ ] Foreign keys work: Try invalid vendor_id

**Key Decisions:**

- Use BIGSERIAL for ride_id (expecting millions of rows)
- Use NUMERIC(8,2) for money (precision matters)
- Use TIMESTAMP (not WITH TIME ZONE - all data is EST)
- Create composite index for datetime + location queries

**Documentation:** See `docs/human/DATABASE.md`

---

### Step 4: Configuration Setup ⏳

**Goal:** Set up environment configuration and database connection

**Files to Create:**

- `.env` - Environment variables (gitignored)
- `.env.example` - Template for others
- `config/database.py` - Database configuration class
- `.gitignore` - Ignore sensitive files

**Tasks:**

1. Create `.env` with database credentials
2. Create `DatabaseConfig` class using python-dotenv
3. Implement connection string generation
4. Add SQLAlchemy engine factory

**Verification:**

- [ ] Can import DatabaseConfig
- [ ] Connection string correct
- [ ] Can create engine: `config.get_engine()`

---

### Step 5: Data Download ⏳

**Goal:** Download NYC taxi dataset

**Tasks:**

1. Create `data/` directory
2. Download November 2024 parquet file
3. Verify file size and integrity

**Commands:**

```bash
mkdir -p data
cd data
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-11.parquet
ls -lh yellow_tripdata_2024-11.parquet
```

**Verification:**

- [ ] File exists in `data/` folder
- [ ] File size reasonable (~40-50 MB for one month)
- [ ] Can open in pandas: `pd.read_parquet('data/yellow_tripdata_2024-11.parquet')`

---

### Step 6: ETL Pipeline Development ⏳

**Goal:** Create Python script to load data into PostgreSQL

**Files to Create:**

- `src/etl/load_data.py` - Main ETL script
- `src/etl/__init__.py` - Package marker

**Tasks:**

1. Create `TaxiDataLoader` class
2. Implement `load_parquet()` - Read parquet file
3. Implement `clean_data()` - Data validation and cleaning
4. Implement `load_to_postgres()` - Batch insert using execute_batch
5. Implement `run_etl()` - Orchestrate the pipeline
6. Add progress logging

**Data Cleaning Rules:**

- Remove: fare_amount <= 0
- Remove: trip_distance <= 0
- Remove: passenger_count <= 0
- Remove: pickup_datetime >= dropoff_datetime
- Remove: NULL in required fields

**Verification:**

- [ ] Can load sample: 1000 rows
- [ ] Data validation works
- [ ] Batch insert efficient
- [ ] No duplicate rides

**Performance Target:** > 10,000 rows/second

---

### Step 7: Initial Data Load ⏳

**Goal:** Load first batch of data (100k rows for development)

**Tasks:**

1. Run ETL with sample_size=100000
2. Verify data in database
3. Check data quality
4. Update table statistics

**Commands:**

```bash
python src/etl/load_data.py
```

**Verification Queries:**

```sql
-- Row count
SELECT COUNT(*) FROM rides;

-- Data quality check
SELECT
    COUNT(*) as total_rows,
    MIN(pickup_datetime) as earliest,
    MAX(pickup_datetime) as latest,
    AVG(total_amount) as avg_fare
FROM rides;

-- Check for invalid data
SELECT COUNT(*) FROM rides
WHERE fare_amount <= 0 OR trip_distance <= 0;
```

**Verification:**

- [ ] ~100k rows loaded
- [ ] No invalid data
- [ ] Dates reasonable
- [ ] Amounts reasonable

---

### Step 8: Zone Data Population ⏳

**Goal:** Load NYC taxi zone lookup data

**Tasks:**

1. Download zone lookup CSV
2. Create script to load zones
3. Verify all location IDs in rides exist in zones

**Commands:**

```bash
# Download zone lookup
wget https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv -O data/taxi_zone_lookup.csv

# Load zones (create script)
python src/etl/load_zones.py
```

**Verification:**

- [ ] 265+ zones loaded
- [ ] All boroughs present
- [ ] Can join rides with zones successfully

---

## 📊 PHASE 2: Analysis & Queries

### Step 9: Basic Analytics Queries 📋

**Goal:** Write fundamental analysis queries

**Files to Create:**

- `sql/queries/basic_analytics.sql`

**Queries to Write:**

1. Average fare per distance
2. Average fare per time (duration)
3. Peak hours per day of week
4. Top 20 pickup zones
5. Top 20 dropoff zones
6. Vendor performance comparison
7. Payment type distribution
8. Passenger count distribution

**Performance Check:**

- Run EXPLAIN ANALYZE on each query
- Ensure indexes are being used
- Target: < 100ms for most queries

**Documentation:** Add to `docs/human/ANALYTICS.md`

---

### Step 10: Advanced Analytics Queries 📋

**Goal:** Implement complex analytical queries

**Files to Create:**

- `sql/queries/advanced_analytics.sql`

**Queries to Write:**

1. **Window Functions:**
   - Ranking drivers by revenue per day
   - Running totals by date
   - Moving averages (7-day, 30-day)
   - Lag/Lead for period-over-period comparison

2. **CTEs (Common Table Expressions):**
   - Multi-step aggregations
   - Recursive queries (if applicable)
   - Complex filtering logic

3. **Time-Series Analysis:**
   - Hourly patterns by day of week
   - Week-over-week growth
   - Seasonal trends

**Example - Ranking Query:**

```sql
SELECT
    vendor_name,
    DATE(pickup_datetime) as date,
    COUNT(*) as trips,
    SUM(total_amount) as revenue,
    RANK() OVER (PARTITION BY DATE(pickup_datetime)
                 ORDER BY SUM(total_amount) DESC) as rank
FROM rides r
JOIN vendors v ON r.vendor_id = v.vendor_id
GROUP BY vendor_name, date;
```

---

### Step 11: Query Optimization 📋

**Goal:** Optimize slow queries using indexes and EXPLAIN ANALYZE

**Tasks:**

1. Identify slow queries (> 1 second)
2. Run EXPLAIN ANALYZE on each
3. Add indexes where beneficial
4. Rewrite inefficient queries
5. Document improvements

**Optimization Techniques:**

- Replace DATE() functions with range comparisons
- Use indexed columns in WHERE clauses
- Consider partial indexes for filtered queries
- Use covering indexes where beneficial

**File to Create:**

- `sql/indexes.sql` - Additional optimization indexes

**Performance Targets:**

- Basic queries: < 100ms
- Complex aggregations: < 500ms
- Full table scans: < 2 seconds (for 100k rows)

---

### Step 12: Materialized Views 📋

**Goal:** Create materialized views for recurring reports

**Files to Create:**

- `sql/views.sql`

**Views to Create:**

1. Daily summary stats
2. Hourly patterns
3. Top locations (pickup/dropoff)
4. Vendor performance metrics

**Example:**

```sql
CREATE MATERIALIZED VIEW daily_summary AS
SELECT
    DATE(pickup_datetime) as date,
    COUNT(*) as total_trips,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_fare,
    AVG(trip_distance) as avg_distance
FROM rides
GROUP BY date;

CREATE INDEX idx_daily_summary_date ON daily_summary(date);

-- Refresh command
REFRESH MATERIALIZED VIEW daily_summary;
```

**Refresh Strategy:**

- Manual refresh after each data load
- Or schedule with cron (future)

---

## 🔌 PHASE 3: API Layer

### Step 13: FastAPI Setup 📋

**Goal:** Initialize FastAPI application structure

**Files to Create:**

- `src/api/main.py` - Main FastAPI app
- `src/api/models.py` - Pydantic models
- `src/api/routes/__init__.py`
- `src/api/services/__init__.py`

**Tasks:**

1. Create FastAPI app instance
2. Configure CORS
3. Add health check endpoint
4. Set up automatic API docs
5. Add database dependency injection

**Basic Structure:**

```python
from fastapi import FastAPI

app = FastAPI(
    title="City Rides Analytics API",
    version="0.1.0",
    description="NYC Taxi Data Analytics API"
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Verification:**

- [ ] Server starts: `uvicorn src.api.main:app --reload`
- [ ] Can access: <http://localhost:8000>
- [ ] Docs available: <http://localhost:8000/docs>

---

### Step 14: CRUD Endpoints 📋

**Goal:** Create basic CRUD endpoints for rides

**Files to Create:**

- `src/api/routes/rides.py`

**Endpoints to Implement:**

1. GET `/api/v1/rides` - List rides (paginated)
2. GET `/api/v1/rides/{ride_id}` - Get single ride
3. GET `/api/v1/rides/search` - Search with filters

**Features:**

- Pagination (limit, offset)
- Filtering (vendor, date range, location)
- Sorting
- Field selection

**Verification:**

- [ ] Can list rides
- [ ] Pagination works
- [ ] Filters work
- [ ] Returns correct data

---

### Step 15: Analytics Endpoints 📋

**Goal:** Create endpoints for analytics queries

**Files to Create:**

- `src/api/routes/analytics.py`

**Endpoints to Implement:**

1. GET `/api/v1/analytics/summary` - Overall statistics
2. GET `/api/v1/analytics/hourly` - Hourly patterns
3. GET `/api/v1/analytics/daily` - Daily statistics
4. GET `/api/v1/analytics/top-locations` - Popular zones
5. GET `/api/v1/analytics/revenue` - Revenue analysis

**Response Format:**

```json
{
  "data": [...],
  "metadata": {
    "count": 100,
    "period": "2024-11-01 to 2024-11-30"
  }
}
```

---

### Step 16: Authentication & Authorization 📋

**Goal:** Add API authentication

**Options:**

1. API Key authentication (simple)
2. OAuth2 with JWT (standard)
3. No auth (if internal only)

**For this project:** Start with API key, prepare for JWT

**Tasks:**

1. Create API key middleware
2. Add authentication dependency
3. Protect endpoints
4. Add rate limiting (optional)

---

## 📊 PHASE 4: Visualization

### Step 17: Dashboard Tool Selection 📋

**Goal:** Choose and set up BI tool

**Options:**

1. **Metabase** (easier, open-source)
2. **Apache Superset** (more powerful, steeper learning curve)
3. **Streamlit** (Python-based, custom)

**Recommendation:** Start with Metabase

**Installation:**

```bash
docker run -d -p 3000:3000 --name metabase metabase/metabase
```

**Verification:**

- [ ] Metabase running: <http://localhost:3000>
- [ ] Can connect to PostgreSQL
- [ ] Can query rides table

---

### Step 18: Dashboard Creation 📋

**Goal:** Build interactive analytics dashboard

**Dashboards to Create:**

1. **Overview Dashboard:**
   - Total trips (current period)
   - Total revenue
   - Average fare
   - Top locations
   - Trend charts

2. **Time Analysis Dashboard:**
   - Trips by hour (heatmap)
   - Daily trends (line chart)
   - Day of week patterns (bar chart)
   - Peak hours indicator

3. **Location Dashboard:**
   - Top pickup zones (map/table)
   - Top dropoff zones (map/table)
   - Popular routes (sankey diagram)
   - Borough comparison

4. **Financial Dashboard:**
   - Revenue trends
   - Payment type distribution
   - Tip analysis (credit card only)
   - Fare distribution

**Interactive Filters:**

- Date range picker
- Vendor selection
- Borough filter
- Payment type filter

---

### Step 19: Dashboard Optimization 📋

**Goal:** Improve dashboard performance

**Tasks:**

1. Use materialized views for dashboard queries
2. Add caching
3. Optimize slow queries
4. Add data refresh schedule

---

## 🚀 PHASE 5: Advanced Features & Optimization

### Step 20: Full Dataset Load 📋

**Goal:** Load complete dataset (3M rows)

**Tasks:**

1. Run ETL without sample_size limit
2. Monitor performance
3. Verify data integrity
4. Update statistics

**Expected Duration:** 5-10 minutes

**Verification:**

- [ ] ~3M rows loaded
- [ ] No data corruption
- [ ] Queries still performant

---

### Step 21: Advanced Indexing 📋

**Goal:** Optimize for full dataset scale

**Tasks:**

1. Analyze query patterns
2. Add covering indexes
3. Consider partial indexes
4. Add GIN indexes if needed (for JSONB in future)

**Performance Benchmark:**

- Re-run all queries
- Compare before/after
- Document improvements

---

### Step 22: Caching Layer 📋

**Goal:** Add Redis for caching frequently accessed data

**Installation:**

```bash
docker run -d -p 6379:6379 --name redis redis
pip install redis
```

**What to Cache:**

- Analytics summaries (TTL: 5 min)
- Top locations (TTL: 1 hour)
- Vendor metrics (TTL: 1 hour)
- Zone lookups (TTL: 1 day)

**Cache Strategy:**

- Cache-aside pattern
- Automatic invalidation on data updates
- Configurable TTLs

---

### Step 23: Monitoring & Logging 📋

**Goal:** Add proper observability

**Tasks:**

1. Replace print statements with proper logging
2. Add application metrics
3. Set up query monitoring
4. Create alerts for issues

**Tools:**

- Python logging module
- PostgreSQL pg_stat_statements
- Optional: Prometheus + Grafana

---

### Step 24: Testing Suite 📋

**Goal:** Add comprehensive tests

**Files to Create:**

- `tests/test_etl.py` - ETL pipeline tests
- `tests/test_api.py` - API endpoint tests
- `tests/test_queries.py` - SQL query tests

**Test Categories:**

1. Unit tests (individual functions)
2. Integration tests (database operations)
3. API tests (endpoint responses)
4. Performance tests (query speed)

**Framework:** pytest

```bash
pip install pytest pytest-cov
pytest tests/ --cov=src
```

---

### Step 25: Documentation Finalization 📋

**Goal:** Complete all documentation

**Tasks:**

1. Update README with complete instructions
2. Document all API endpoints
3. Add code comments
4. Create architecture diagram
5. Write deployment guide

---

## 🎯 Stretch Goals (Optional)

### Advanced Features

1. **Airflow ETL Orchestration:**
   - Schedule monthly data downloads
   - Automate ETL pipeline
   - Handle failures and retries

2. **TimescaleDB Integration:**
   - Convert to hypertables
   - Use time-series specific features
   - Improve time-based query performance

3. **Machine Learning:**
   - Fare prediction model
   - Demand forecasting
   - Anomaly detection

4. **Real-time Data:**
   - Streaming data ingestion (Kafka)
   - Real-time dashboard updates
   - WebSocket API

5. **Multi-source Integration:**
   - Add Uber data
   - Add Lyft data
   - Cross-platform analysis

6. **Advanced Visualizations:**
   - Geographic heatmaps
   - 3D visualizations
   - Animation over time

7. **Deployment:**
   - Docker containerization
   - Kubernetes orchestration
   - CI/CD pipeline
   - Cloud deployment (AWS/Azure/GCP)

---

## ✅ Progress Tracking

### Phase 1: Foundation

- [x] Step 1: Environment Setup
- [x] Step 2: Database Creation
- [ ] Step 3: Schema Implementation
- [ ] Step 4: Configuration Setup
- [ ] Step 5: Data Download
- [ ] Step 6: ETL Development
- [ ] Step 7: Initial Data Load
- [ ] Step 8: Zone Data Population

### Phase 2: Analysis

- [ ] Step 9: Basic Analytics
- [ ] Step 10: Advanced Analytics
- [ ] Step 11: Query Optimization
- [ ] Step 12: Materialized Views

### Phase 3: API

- [ ] Step 13: FastAPI Setup
- [ ] Step 14: CRUD Endpoints
- [ ] Step 15: Analytics Endpoints
- [ ] Step 16: Authentication

### Phase 4: Visualization

- [ ] Step 17: Tool Selection
- [ ] Step 18: Dashboard Creation
- [ ] Step 19: Dashboard Optimization

### Phase 5: Optimization

- [ ] Step 20: Full Dataset Load
- [ ] Step 21: Advanced Indexing
- [ ] Step 22: Caching Layer
- [ ] Step 23: Monitoring
- [ ] Step 24: Testing Suite
- [ ] Step 25: Documentation

---

**Next Step:** Complete Step 3 - Schema Implementation

**Last Updated:** November 2, 2025
