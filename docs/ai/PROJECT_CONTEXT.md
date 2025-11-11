# Project Context - AI Assistant Reference

## 🎯 Project Purpose

This is a data analytics project designed to analyze NYC Yellow Taxi trip data. The project demonstrates:

- PostgreSQL database design and optimization
- ETL pipeline development with Python
- Data analysis using SQL (window functions, CTEs, aggregations)
- RESTful API development with FastAPI
- Data visualization and dashboard creation with Metabase

**Target Audience:** Data engineers, data analysts, backend developers learning data engineering concepts.

**Current Status:** Phase 3 Complete (API Layer), Phase 4 In Progress (Dashboard Creation)

## 📐 Architecture Overview

### Technology Stack

- **Database:** PostgreSQL 14+ (with extensions: btree_gin)
- **ETL:** Python 3.9+ with pandas, pyarrow for parquet files
- **ORM/DB Access:** SQLAlchemy, psycopg2-binary
- **API:** FastAPI 0.104+, Uvicorn (ASGI server)
- **Visualization:** Metabase (Docker container)
- **Environment:** python-dotenv for configuration

### Data Flow

```text
Raw Data (Parquet) → Python ETL → PostgreSQL → API/Analytics → Visualization
```

1. **Ingestion:** Monthly parquet files from NYC TLC (~3M rows)
2. **Transformation:** Data cleaning, validation, type conversion in Python
3. **Loading:** Batch insert using psycopg2 execute_batch
4. **Storage:** PostgreSQL with optimized indexes
5. **Analysis:** SQL queries for insights
6. **Access:** FastAPI REST endpoints
7. **Presentation:** BI dashboard (future)

## 📊 Database Design

### Schema Pattern

Star schema with fact and dimension tables:

- **Fact Table:** `rides` (main transactional data)
- **Dimension Tables:** `vendors`, `zones`

### Key Design Decisions

1. **Serial ID vs Natural Key:**
   - Used `BIGSERIAL` for `ride_id` as primary key
   - Original data has no unique identifier
   - Enables easier referencing and indexing

2. **Indexing Strategy:**
   - B-tree indexes on frequently queried columns (datetime, location)
   - Composite index for common query patterns (datetime + location)
   - No full-text search indexes (not needed for this use case)

3. **Data Types:**
   - `TIMESTAMP` for datetime (not WITH TIME ZONE - all data is EST)
   - `NUMERIC(8,2)` for money values (precision important)
   - `INTEGER` for foreign keys and counts
   - `CHAR(1)` for single-character flags

4. **Normalization:**
   - Vendors normalized to separate table (lookup data)
   - Zones normalized to separate table (NYC TLC reference data)
   - Rides denormalized for query performance

5. **Constraints:**
   - Foreign keys to maintain referential integrity
   - NOT NULL on critical fields (datetime, vendor_id)
   - No CHECK constraints (validation done in ETL)

## 🔄 ETL Pipeline Design

### ETL Strategy

**Extract:**

- Read parquet files using pyarrow (faster than pandas alone)
- Support for sampling (100k rows for dev, full for prod)

**Transform:**

- Column renaming to match schema
- Data type conversion
- Data validation (positive values, valid timestamps)
- Null handling (drop or fill based on column)

**Load:**

- Batch insert using `execute_batch` (faster than individual inserts)
- Configurable batch size (default: 1000 rows)
- Transaction management (commit on success, rollback on error)
- Progress logging

### Data Validation Rules

**Remove records where:**

- `fare_amount <= 0`
- `trip_distance <= 0`
- `passenger_count <= 0`
- `pickup_datetime >= dropoff_datetime`
- NULL in required fields (pickup_datetime, dropoff_datetime, vendor_id)

**Keep records even if:**

- `tip_amount = 0` (cash payments don't record tips)
- `passenger_count` is unusually high (edge case, not invalid)
- Location IDs are NULL (some trips have unknown locations)

## 🗂️ File Organization

### Directory Structure Logic

```text
/
├── data/               # Gitignored - large files
├── sql/                # Version controlled SQL scripts
│   ├── schema.sql     # Table definitions, indexes
│   └── queries/       # Analysis queries by category
├── src/                # Python source code
│   ├── etl/           # ETL scripts
│   ├── api/           # FastAPI application
│   └── analytics/     # Analytics modules
├── config/             # Configuration modules
├── docs/               # Documentation
│   ├── human/         # User-facing docs
│   └── ai/            # AI assistant context
├── notebooks/          # Jupyter notebooks for exploration
└── tests/              # Test suite
```

### File Naming Conventions

- **SQL files:** `snake_case.sql` (e.g., `basic_analytics.sql`)
- **Python modules:** `snake_case.py` (e.g., `load_data.py`)
- **Classes:** `PascalCase` (e.g., `TaxiDataLoader`)
- **Functions:** `snake_case` (e.g., `clean_data`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `BATCH_SIZE`)

## 🔧 Configuration Management

### Environment Variables

Stored in `.env` file (never committed):

- Database credentials
- API configuration
- ETL parameters
- Logging settings

### Configuration Loading

- `python-dotenv` loads `.env` at runtime
- `DatabaseConfig` class centralizes DB config
- Environment-specific configs (dev/prod) planned for future

## 📈 Query Optimization Strategy

### Performance Considerations

1. **Indexed Columns:**
   - Always use indexed columns in WHERE clauses
   - Prefer `pickup_datetime` over `dropoff_datetime` when possible
   - Use composite index for combined filters

2. **Aggregation:**
   - Use GROUP BY with indexed columns
   - Consider materialized views for recurring aggregations
   - Avoid COUNT(\*) on full table (use pg_stat_user_tables)

3. **Joins:**
   - Vendor and zone joins are cheap (small lookup tables)
   - Always join on indexed foreign keys
   - Use LEFT JOIN when including zero-count locations

4. **Window Functions:**
   - Partition by indexed columns when possible
   - Use ROWS vs RANGE carefully (ROWS is faster)
   - Consider LIMIT for large result sets

## 🐛 Common Issues & Solutions

### Issue: ETL Fails with Memory Error

**Solution:** Reduce `sample_size` or process in chunks

### Issue: Slow Query Performance

**Solution:**

1. Run `EXPLAIN ANALYZE` to check execution plan
2. Verify indexes are being used
3. Update table statistics with `ANALYZE`

### Issue: Foreign Key Constraint Violation

**Solution:** Ensure vendor and zone tables are populated before loading rides

### Issue: Database Connection Fails

**Solution:**

1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify credentials in `.env`
3. Check `pg_hba.conf` for authentication method

## 🔄 Development Workflow

### Typical Development Flow

1. **Schema Changes:**
   - Update `sql/schema.sql`
   - Document change in migration notes
   - Test with sample data
   - Apply to production

2. **Adding New Query:**
   - Write query in `sql/queries/`
   - Test with `EXPLAIN ANALYZE`
   - Add to API endpoint if needed
   - Document in ANALYTICS.md

3. **ETL Modifications:**
   - Update `src/etl/load_data.py`
   - Test with small sample first
   - Validate data integrity
   - Run full load

4. **API Development:**
   - Add endpoint to `src/api/routes/`
   - Define Pydantic models in `src/api/models.py`
   - Update API.md documentation
   - Test with curl/httpie

## 📦 Dependencies Rationale

### Core Dependencies

- **psycopg2-binary:** PostgreSQL adapter (binary for easy install)
- **pandas:** Data manipulation (familiar API, good for ETL)
- **pyarrow:** Parquet file reading (faster than pandas alone)
- **SQLAlchemy:** ORM and connection management (not used for ORM yet, just engine)
- **python-dotenv:** Environment variable management
- **FastAPI:** Modern async API framework with auto-docs
- **uvicorn:** ASGI server for FastAPI

### Why These Choices?

- **pandas over pure Python:** Faster operations, easier data cleaning
- **pyarrow over pandas parquet:** Better performance for parquet files
- **FastAPI over Flask:** Auto-validation, async support, built-in docs
- **psycopg2 over asyncpg:** Simpler for beginners, synchronous is fine for batch ETL

## 🎯 Project Phases

### Phase 1: Foundation ✅ COMPLETED

- Database setup
- Schema design
- Basic ETL pipeline
- Initial data load (93,171 rides)

### Phase 2: Analysis ✅ COMPLETED

- Write analysis queries
- Optimize performance
- Create materialized views (8 views)
- Performance monitoring

### Phase 3: API Layer ✅ COMPLETED

- FastAPI implementation (13 endpoints)
- CRUD endpoints
- Analytics endpoints
- Automatic documentation
- Error handling and logging

### Phase 4: Visualization 🚧 IN PROGRESS

- Metabase installation ✅
- Database connection ✅
- Dashboard design ✅
- Dashboard creation (pending)
- Interactive filters (pending)

### Phase 5: Optimization (Future)

- Query optimization
- Caching layer (Redis)
- Connection pooling
- Monitoring

## 🔮 Future Enhancements

### Planned Features

- TimescaleDB extension for time-series optimization
- Airflow for ETL orchestration
- Docker containerization
- CI/CD pipeline
- Additional data sources (Uber, Lyft)
- Machine learning predictions (fare estimation, demand forecasting)

### Technical Debt to Address

- Add comprehensive test suite (pytest)
- Implement proper logging (not just prints)
- Add data quality monitoring
- Create database migration system
- Implement proper error handling in API

---

**Last Updated:** November 9, 2025
**Project Status:** Phase 3 Complete - API Layer Operational
