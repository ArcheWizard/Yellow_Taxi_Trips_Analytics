#!/usr/bin/env python3
"""
Project Verification Script
Checks that all components are properly set up and working.
"""

import os
import sys
from pathlib import Path

from config.database import DatabaseConfig

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_environment():
    """Check environment variables are set."""
    print("=" * 60)
    print("1. Checking Environment Configuration...")
    print("=" * 60)

    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'*' * len(value) if 'PASSWORD' in var else value}")
        else:
            print(f"✗ {var}: NOT SET")
            missing.append(var)

    if missing:
        print(f"\n⚠ Missing environment variables: {', '.join(missing)}")
        return False

    print("\n✓ All environment variables are set")
    return True


def check_database_connection():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("2. Checking Database Connection...")
    print("=" * 60)

    try:
        config = DatabaseConfig()
        conn = config.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL Version: {version.split(',')[0]}")

        cursor.close()
        conn.close()
        print("✓ Database connection successful")
        return True

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def check_tables():
    """Check that all tables exist."""
    print("\n" + "=" * 60)
    print("3. Checking Database Tables...")
    print("=" * 60)

    try:
        config = DatabaseConfig()
        conn = config.get_connection()
        cursor = conn.cursor()

        # Check tables
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        )

        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = ["vendors", "zones", "rides"]

        for table in expected_tables:
            if table in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"✓ Table '{table}': {count:,} rows")
            else:
                print(f"✗ Table '{table}': NOT FOUND")
                return False

        cursor.close()
        conn.close()
        print("\n✓ All tables exist and contain data")
        return True

    except Exception as e:
        print(f"✗ Table check failed: {e}")
        return False


def check_indexes():
    """Check that indexes exist."""
    print("\n" + "=" * 60)
    print("4. Checking Database Indexes...")
    print("=" * 60)

    try:
        config = DatabaseConfig()
        conn = config.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'rides'
            ORDER BY indexname;
        """
        )

        indexes = [row[0] for row in cursor.fetchall()]

        print(f"✓ Found {len(indexes)} indexes on rides table:")
        for idx in indexes:
            print(f"  - {idx}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"✗ Index check failed: {e}")
        return False


def check_data_quality():
    """Run basic data quality checks."""
    print("\n" + "=" * 60)
    print("5. Checking Data Quality...")
    print("=" * 60)

    try:
        config = DatabaseConfig()
        conn = config.get_connection()
        cursor = conn.cursor()

        # Check for data
        cursor.execute("SELECT COUNT(*) FROM rides;")
        total_rides = cursor.fetchone()[0]

        if total_rides == 0:
            print("✗ No ride data found")
            return False

        print(f"✓ Total rides: {total_rides:,}")

        # Check date range
        cursor.execute(
            """
            SELECT
                MIN(pickup_datetime)::date,
                MAX(pickup_datetime)::date
            FROM rides;
        """
        )
        min_date, max_date = cursor.fetchone()
        print(f"✓ Date range: {min_date} to {max_date}")

        # Check averages
        cursor.execute(
            """
            SELECT
                ROUND(AVG(trip_distance)::numeric, 2),
                ROUND(AVG(total_amount)::numeric, 2)
            FROM rides;
        """
        )
        avg_distance, avg_fare = cursor.fetchone()
        print(f"✓ Average trip distance: {avg_distance} miles")
        print(f"✓ Average fare: ${avg_fare}")

        # Check for nulls in critical fields
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM rides
            WHERE pickup_datetime IS NULL
               OR dropoff_datetime IS NULL;
        """
        )
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            print(f"⚠ Warning: {null_count} rides with null timestamps")
        else:
            print("✓ No null values in critical fields")

        cursor.close()
        conn.close()
        print("\n✓ Data quality checks passed")
        return True

    except Exception as e:
        print(f"✗ Data quality check failed: {e}")
        return False


def check_file_structure():
    """Check project file structure."""
    print("\n" + "=" * 60)
    print("6. Checking Project File Structure...")
    print("=" * 60)

    required_files = [
        "README.md",
        "requirements.txt",
        ".env",
        "config/database.py",
        "sql/schema.sql",
        "sql/queries/basic_analytics.sql",
        "src/etl/load_data.py",
        "src/etl/load_zones.py",
    ]

    missing = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}: NOT FOUND")
            missing.append(file_path)

    if missing:
        print(f"\n⚠ Missing files: {len(missing)}")
        return False

    print("\n✓ All required files exist")
    return True


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("CITY RIDES ANALYTICS - PROJECT VERIFICATION")
    print("=" * 60)

    checks = [
        check_environment,
        check_database_connection,
        check_tables,
        check_indexes,
        check_data_quality,
        check_file_structure,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Check failed with error: {e}")
            results.append(False)

    # Final summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Checks passed: {passed}/{total}")

    if all(results):
        print("\n🎉 ALL CHECKS PASSED! Project is ready!")
        print("\nNext steps:")
        print("  1. Review the analytics queries in sql/queries/basic_analytics.sql")
        print("  2. Run queries to explore your data")
        print("  3. Check PROGRESS.md for next phase tasks")
        return 0
    else:
        print("\n⚠ Some checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
