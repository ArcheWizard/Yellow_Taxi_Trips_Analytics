"""
Load all parquet files from the data directory into PostgreSQL.
Processes each file completely (no sampling).
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseConfig
from src.etl.load_data import TaxiDataLoader


def get_current_row_count(db):
    """Get current row count in rides table."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rides;")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    finally:
        db.return_connection(conn)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║         Load All Parquet Files into PostgreSQL                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    data_dir = Path("data")
    db = DatabaseConfig()
    loader = TaxiDataLoader()

    # Get initial count
    initial_count = get_current_row_count(db)
    print(f"Initial row count: {initial_count:,}\n")

    # Get all parquet files
    parquet_files = sorted(data_dir.glob("yellow_tripdata_*.parquet"))

    if not parquet_files:
        print("✗ No parquet files found in data/ directory")
        return

    print(f"Found {len(parquet_files)} parquet files:\n")
    for f in parquet_files:
        size_mb = f.stat().st_size / (1024**2)
        print(f"  - {f.name} ({size_mb:.1f} MB)")

    print("\n" + "=" * 70)
    print("Starting data load...")
    print("=" * 70 + "\n")

    total_start = time.time()
    loaded_count = 0

    for i, file in enumerate(parquet_files, 1):
        # Skip empty files
        if file.stat().st_size == 0:
            print(f"[{i}/{len(parquet_files)}] Skipping {file.name} (empty file)\n")
            continue

        print(f"[{i}/{len(parquet_files)}] Loading {file.name}...")

        try:
            start_time = time.time()

            # Load entire file (no sampling)
            loader.run_etl(str(file), sample_size=None)

            duration = time.time() - start_time

            # Get new count
            new_count = get_current_row_count(db)
            rows_added = new_count - initial_count - loaded_count
            loaded_count += rows_added

            print(f"  ✓ Loaded {rows_added:,} rows in {duration:.1f}s")
            print(f"  Total so far: {initial_count + loaded_count:,} rows\n")

        except Exception as e:
            print(f"  ✗ Error loading {file.name}: {e}\n")
            continue

    total_duration = time.time() - total_start
    final_count = get_current_row_count(db)

    print("=" * 70)
    print("LOAD COMPLETE")
    print("=" * 70)
    print(f"Initial rows:    {initial_count:,}")
    print(f"Rows loaded:     {loaded_count:,}")
    print(f"Final rows:      {final_count:,}")
    print(f"Total time:      {total_duration / 60:.1f} minutes")
    print("=" * 70)

    # Refresh materialized views
    print("\nRefreshing materialized views...")
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT refresh_all_incremental_mv();")
        conn.commit()
        cursor.close()
        db.return_connection(conn)
        print("✓ Materialized views refreshed")
    except Exception as e:
        print(f"⚠️  Failed to refresh views: {e}")

    print("\n✓ All data loaded successfully!")


if __name__ == "__main__":
    main()
