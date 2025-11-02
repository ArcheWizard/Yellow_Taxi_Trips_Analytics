#!/usr/bin/env python3
"""
Load Taxi Zone Lookup Data
This script loads the NYC taxi zone lookup data into the zones table.
"""

import sys
from pathlib import Path

import pandas as pd

from config.database import DatabaseConfig

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_zones():
    """Load taxi zone data from CSV file into the zones table."""
    print("Starting zone data load...")

    # Initialize database config
    db_config = DatabaseConfig()

    # Get the actual project root (parent of parent of this file)
    zones_file = Path(__file__).parent.parent.parent / "data" / "taxi_zone_lookup.csv"

    if not zones_file.exists():
        print(f"Error: Zone file not found at {zones_file}")
        return False

    print(f"Reading zone data from {zones_file}...")
    df = pd.read_csv(zones_file)

    # Rename columns to match schema
    column_mapping = {
        "LocationID": "location_id",
        "Borough": "borough",
        "Zone": "zone",
        "service_zone": "service_zone",
    }
    df = df.rename(columns=column_mapping)

    print(f"Loaded {len(df)} zones from CSV")
    print("\nSample data:")
    print(df.head())

    # Connect to database
    try:
        conn = db_config.get_connection()
        if not conn:
            print("Error: Could not connect to database")
            return False

        cursor = conn.cursor()

        # Clear existing zones (if any)
        cursor.execute("DELETE FROM zones;")
        print("\nCleared existing zone data")

        # Insert zones
        insert_query = """
            INSERT INTO zones (location_id, borough, zone, service_zone)
            VALUES (%s, %s, %s, %s)
        """

        # Convert to list of tuples with Python native types
        data = []
        for _, row in df.iterrows():
            data.append(
                (
                    int(row["location_id"]),
                    str(row["borough"]),
                    str(row["zone"]),
                    str(row["service_zone"]),
                )
            )

        cursor.executemany(insert_query, data)
        conn.commit()

        print(f"\nInserted {len(data)} zones into database")

        # Verify the load
        cursor.execute("SELECT COUNT(*) FROM zones;")
        count = cursor.fetchone()[0]
        print(f"Verification: {count} zones in database")

        # Show sample
        cursor.execute("SELECT * FROM zones LIMIT 5;")
        print("\nSample zones in database:")
        for row in cursor.fetchall():
            print(row)

        cursor.close()
        conn.close()

        print("\n✓ Zone data loaded successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Error loading zone data: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = load_zones()
    sys.exit(0 if success else 1)
