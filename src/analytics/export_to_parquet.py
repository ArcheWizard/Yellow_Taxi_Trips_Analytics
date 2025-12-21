"""
Export PostgreSQL data to Parquet format for DuckDB analysis.
This script extracts the rides table and exports it to columnar Parquet files.
"""

import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseConfig


def export_rides_to_parquet(output_dir: str = "data/parquet"):
    """Export rides table to Parquet format."""

    db = DatabaseConfig()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           Export PostgreSQL Data to Parquet Format                   ║
║                                                                       ║
║  This exports the rides table to columnar Parquet storage for        ║
║  DuckDB analysis and comparison.                                     ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        # Get total row count
        print("Getting row count...")
        cursor.execute("SELECT COUNT(*) FROM rides;")
        total_rows = cursor.fetchone()[0]
        print(f"Total rows to export: {total_rows:,}\n")

        # Export in chunks for memory efficiency
        chunk_size = 100000
        print(f"Exporting in chunks of {chunk_size:,} rows...\n")

        # Get column names
        cursor.execute("SELECT * FROM rides LIMIT 0;")
        columns = [desc[0] for desc in cursor.description]

        offset = 0
        chunk_num = 0

        while offset < total_rows:
            chunk_num += 1
            print(
                f"Chunk {chunk_num}: Rows {offset:,} to {min(offset + chunk_size, total_rows):,}..."
            )

            # Fetch chunk
            query = f"""
                SELECT * FROM rides
                ORDER BY ride_id
                LIMIT {chunk_size} OFFSET {offset};
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            if not rows:
                break

            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=columns)

            # Save as Parquet
            output_file = output_path / f"rides_chunk_{chunk_num:03d}.parquet"
            df.to_parquet(
                output_file, engine="pyarrow", compression="snappy", index=False
            )

            print(f"  ✓ Saved {len(rows):,} rows to {output_file.name}")

            offset += chunk_size

        cursor.close()

        # Also export zones table (small, single file)
        print("\nExporting zones table...")
        zones_df = pd.read_sql("SELECT * FROM zones;", conn)
        zones_file = output_path / "zones.parquet"
        zones_df.to_parquet(
            zones_file, engine="pyarrow", compression="snappy", index=False
        )
        print(f"  ✓ Saved {len(zones_df)} zones to {zones_file.name}")

        # Summary
        print("\n" + "=" * 70)
        print("EXPORT COMPLETE")
        print("=" * 70)
        print(f"Output directory: {output_path.absolute()}")
        print(f"Total files: {chunk_num + 1}")
        print(f"Total rows exported: {total_rows:,}")

        # Get total size
        total_size = sum(f.stat().st_size for f in output_path.glob("*.parquet"))
        print(f"Total size: {total_size / (1024**2):.2f} MB")
        print("=" * 70)

    finally:
        db.return_connection(conn)


if __name__ == "__main__":
    export_rides_to_parquet()
