# Development Guide - AI Assistant Reference

## 🤖 AI Assistant Guidelines

This document provides guidance for AI assistants working on this project. It includes coding standards, common patterns, and best practices specific to this codebase.

## 🎯 Code Modification Principles

### When Making Changes

1. **Always read existing code first** - Understand the current implementation before suggesting changes
2. **Maintain consistency** - Follow existing patterns and naming conventions
3. **Preserve functionality** - Don't break existing features
4. **Consider performance** - Database queries should be efficient
5. **Document changes** - Update relevant documentation files

### What to Preserve

- Database schema structure (don't casually rename columns)
- Existing indexes (don't drop without understanding impact)
- API endpoint contracts (breaking changes affect users)
- Configuration patterns (DatabaseConfig class, .env usage)
- File organization (keep files in correct directories)

### What to Improve

- Query optimization (add indexes, rewrite inefficient queries)
- Error handling (add try-except, validation)
- Code documentation (docstrings, comments)
- Test coverage (add tests for new features)
- Logging (replace prints with proper logging)

## 📝 Python Coding Standards

### Style Guide

- **PEP 8 compliant** - Use standard Python style
- **Line length:** 88 characters (Black formatter standard)
- **Quotes:** Single quotes for strings, double for docstrings
- **Imports:** Grouped (stdlib, third-party, local)

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description of function.

    Longer description if needed, explaining what the function does,
    any important behaviors, or edge cases.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When this happens

    Example:
        >>> function_name('test', 42)
        True
    """
    pass
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import List, Dict, Optional, Tuple

def get_rides(
    limit: int = 100,
    offset: int = 0,
    vendor_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get rides with pagination."""
    pass
```

### Error Handling Pattern

```python
try:
    # Operation that might fail
    result = perform_operation()
except SpecificException as e:
    # Log the error
    logger.error(f"Operation failed: {e}")
    # Handle appropriately
    raise
finally:
    # Cleanup if needed
    cleanup_resources()
```

## 🗄️ SQL Guidelines

### Query Writing Standards

1. **Use explicit column names** - Never use `SELECT *` in production code
2. **Consistent formatting** - Capitalize SQL keywords
3. **Avoid N+1 queries** - Use JOINs instead of loops
4. **Index awareness** - Use indexed columns in WHERE clauses
5. **Comment complex logic** - Explain non-obvious queries

### Query Template

```sql
-- Purpose: Brief description of what this query does
-- Performance: Expected row count, execution time
-- Dependencies: Tables/indexes required

SELECT
    r.ride_id,
    r.pickup_datetime,
    r.total_amount,
    v.vendor_name
FROM rides r
INNER JOIN vendors v ON r.vendor_id = v.vendor_id
WHERE r.pickup_datetime >= %s
  AND r.pickup_datetime < %s
ORDER BY r.pickup_datetime DESC
LIMIT %s OFFSET %s;
```

### When to Use Window Functions

Use window functions when you need:

- Running totals or moving averages
- Ranking within groups
- Access to previous/next row values
- Calculations without grouping

**Example:**

```sql
SELECT
    date,
    revenue,
    AVG(revenue) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7day
FROM daily_stats;
```

### When to Use CTEs

Use CTEs (Common Table Expressions) when:

- Query is complex and needs to be broken down
- Same subquery is used multiple times
- Recursive queries are needed
- Improving readability

**Example:**

```sql
WITH daily_stats AS (
    SELECT
        DATE(pickup_datetime) as date,
        COUNT(*) as trips
    FROM rides
    GROUP BY date
),
avg_stats AS (
    SELECT AVG(trips) as avg_trips
    FROM daily_stats
)
SELECT
    d.date,
    d.trips,
    a.avg_trips,
    d.trips - a.avg_trips as diff_from_avg
FROM daily_stats d
CROSS JOIN avg_stats a;
```

## 🔌 API Development Patterns

### FastAPI Route Structure

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/rides", tags=["rides"])

class RideResponse(BaseModel):
    ride_id: int
    pickup_datetime: datetime
    total_amount: float

    class Config:
        from_attributes = True

@router.get("/", response_model=List[RideResponse])
async def get_rides(
    limit: int = Query(100, ge=1, le=1000, description="Number of records"),
    offset: int = Query(0, ge=0, description="Records to skip"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor")
):
    """
    Get list of rides with pagination.

    - **limit**: Maximum records to return (1-1000)
    - **offset**: Number of records to skip
    - **vendor_id**: Optional vendor filter
    """
    try:
        # Query database
        rides = query_rides(limit, offset, vendor_id)
        return rides
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Pydantic Model Patterns

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class RideCreate(BaseModel):
    """Model for creating a new ride."""
    vendor_id: int = Field(..., ge=1, le=2)
    pickup_datetime: datetime
    dropoff_datetime: datetime
    passenger_count: int = Field(..., ge=1, le=10)
    trip_distance: float = Field(..., gt=0)
    total_amount: float = Field(..., gt=0)

    @validator('dropoff_datetime')
    def dropoff_after_pickup(cls, v, values):
        if 'pickup_datetime' in values and v <= values['pickup_datetime']:
            raise ValueError('Dropoff must be after pickup')
        return v

class RideResponse(RideCreate):
    """Model for ride response with ID."""
    ride_id: int
    created_at: datetime
```

## 🗂️ Database Access Patterns

### Connection Management

```python
from contextlib import contextmanager
from config.database import DatabaseConfig

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    config = DatabaseConfig()
    conn = None
    try:
        conn = psycopg2.connect(config.get_connection_string())
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

# Usage
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rides LIMIT 10")
    results = cursor.fetchall()
```

### Query Execution Pattern

```python
def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """
    Execute a query and return results as list of dicts.

    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters for query

    Returns:
        List of dictionaries with column names as keys
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Convert rows to dicts
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results
```

## 🧪 Testing Guidelines

### Test Structure

```python
import pytest
from src.etl.load_data import TaxiDataLoader

class TestTaxiDataLoader:
    """Test suite for TaxiDataLoader."""

    @pytest.fixture
    def loader(self):
        """Fixture to create loader instance."""
        return TaxiDataLoader()

    def test_load_parquet(self, loader):
        """Test loading parquet file."""
        df = loader.load_parquet('data/test_sample.parquet')
        assert len(df) > 0
        assert 'VendorID' in df.columns

    def test_clean_data_removes_invalid(self, loader):
        """Test that invalid records are removed."""
        # Create test DataFrame with invalid data
        df = create_test_dataframe()
        cleaned = loader.clean_data(df)

        # Verify invalid records removed
        assert all(cleaned['fare_amount'] > 0)
        assert all(cleaned['trip_distance'] > 0)
```

### Query Testing

```sql
-- Test query performance
EXPLAIN ANALYZE
SELECT
    pickup_location_id,
    COUNT(*) as trips
FROM rides
WHERE pickup_datetime >= '2024-11-01'
  AND pickup_datetime < '2024-11-02'
GROUP BY pickup_location_id;

-- Expected: Index scan on idx_rides_pickup_datetime
-- Execution time: < 100ms
```

## 📊 Common Query Patterns

### Pagination

```python
def get_paginated_results(
    base_query: str,
    params: tuple,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """Get paginated query results."""

    # Count total (without LIMIT/OFFSET)
    count_query = f"SELECT COUNT(*) FROM ({base_query}) as subq"
    total = execute_query(count_query, params)[0]['count']

    # Get page of results
    page_query = f"{base_query} LIMIT %s OFFSET %s"
    results = execute_query(page_query, params + (limit, offset))

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'data': results
    }
```

### Date Range Filtering

```python
from datetime import datetime, timedelta

def get_rides_in_range(
    start_date: datetime,
    end_date: datetime,
    limit: int = 1000
) -> List[Dict]:
    """Get rides within date range."""
    query = """
        SELECT
            ride_id,
            pickup_datetime,
            total_amount
        FROM rides
        WHERE pickup_datetime >= %s
          AND pickup_datetime < %s
        ORDER BY pickup_datetime
        LIMIT %s
    """
    return execute_query(query, (start_date, end_date, limit))
```

### Aggregation with Groups

```python
def get_hourly_stats(date: datetime) -> List[Dict]:
    """Get hourly trip statistics for a specific date."""
    query = """
        SELECT
            EXTRACT(HOUR FROM pickup_datetime) as hour,
            COUNT(*) as trip_count,
            AVG(total_amount) as avg_fare,
            SUM(total_amount) as total_revenue
        FROM rides
        WHERE DATE(pickup_datetime) = %s
        GROUP BY hour
        ORDER BY hour
    """
    return execute_query(query, (date.date(),))
```

## 🚨 Error Handling Patterns

### ETL Error Handling

```python
class ETLError(Exception):
    """Base exception for ETL errors."""
    pass

class DataValidationError(ETLError):
    """Raised when data validation fails."""
    pass

class DatabaseLoadError(ETLError):
    """Raised when database load fails."""
    pass

def safe_etl_run(file_path: str):
    """Run ETL with comprehensive error handling."""
    loader = TaxiDataLoader()

    try:
        loader.run_etl(file_path)
    except FileNotFoundError:
        logger.error(f"Data file not found: {file_path}")
        raise
    except DataValidationError as e:
        logger.error(f"Data validation failed: {e}")
        # Maybe send alert
        raise
    except DatabaseLoadError as e:
        logger.error(f"Database load failed: {e}")
        # Rollback, cleanup
        raise
    except Exception as e:
        logger.exception("Unexpected error in ETL")
        raise
```

## 📈 Performance Optimization Checklist

When optimizing queries:

1. **Run EXPLAIN ANALYZE** - See actual execution plan
2. **Check index usage** - Verify indexes are being used
3. **Measure before and after** - Document improvements
4. **Consider table statistics** - Run ANALYZE if needed
5. **Test with production volume** - Sample data may mislead
6. **Monitor memory usage** - Large queries can cause issues
7. **Check for table bloat** - VACUUM if needed

### Optimization Example

```sql
-- Before: Sequential scan, slow
SELECT * FROM rides WHERE DATE(pickup_datetime) = '2024-11-01';

-- After: Index scan, fast
SELECT * FROM rides
WHERE pickup_datetime >= '2024-11-01'
  AND pickup_datetime < '2024-11-02';
```

## 🔄 Migration Pattern (Future)

When schema changes are needed:

```sql
-- migrations/001_add_driver_rating.sql
BEGIN;

-- Add new column
ALTER TABLE rides
ADD COLUMN driver_rating INTEGER;

-- Add check constraint
ALTER TABLE rides
ADD CONSTRAINT check_rating_range
CHECK (driver_rating >= 1 AND driver_rating <= 5);

-- Create index if needed
CREATE INDEX idx_rides_driver_rating
ON rides(driver_rating);

-- Update migration tracking
INSERT INTO schema_migrations (version, applied_at)
VALUES ('001', NOW());

COMMIT;
```

## 📚 Helpful Resources

### SQL Optimization

- PostgreSQL EXPLAIN: <https://www.postgresql.org/docs/current/using-explain.html>
- Index types: <https://www.postgresql.org/docs/current/indexes-types.html>

### Python Best Practices

- PEP 8: <https://pep8.org/>
- Type hints: <https://docs.python.org/3/library/typing.html>

### FastAPI

- Documentation: <https://fastapi.tiangolo.com/>
- Dependency injection: <https://fastapi.tiangolo.com/tutorial/dependencies/>

---

**Last Updated:** November 2, 2025
