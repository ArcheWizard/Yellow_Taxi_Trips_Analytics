"""
ETL Pipeline for NYC Taxi Data.

This module handles loading parquet data, cleaning it, and loading it into PostgreSQL.
"""

import os
import sys
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.database import DatabaseConfig


class TaxiDataLoader:
    """ETL pipeline for loading NYC taxi data into PostgreSQL."""

    def __init__(self):
        """Initialize the data loader with database configuration."""
        self.config = DatabaseConfig()
        self.conn = None

    def connect(self):
        """
        Establish database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
            print("✓ Database connection established")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

    def load_parquet(self, file_path, sample_size=None):
        """
        Load parquet file into pandas DataFrame.

        Args:
            file_path (str): Path to parquet file
            sample_size (int, optional): Number of rows to sample

        Returns:
            DataFrame: Loaded data
        """
        print(f"Loading data from {file_path}...")
        df = pd.read_parquet(file_path)

        if sample_size:
            df = df.head(sample_size)
            print(f"✓ Loaded {len(df):,} rows (sampled)")
        else:
            print(f"✓ Loaded {len(df):,} rows")

        return df

    def clean_data(self, df):
        """
        Clean and validate data.

        Args:
            df (DataFrame): Raw data

        Returns:
            DataFrame: Cleaned data
        """
        print("Cleaning data...")
        initial_rows = len(df)

        # Rename columns to match our schema
        column_mapping = {
            "VendorID": "vendor_id",
            "tpep_pickup_datetime": "pickup_datetime",
            "tpep_dropoff_datetime": "dropoff_datetime",
            "passenger_count": "passenger_count",
            "trip_distance": "trip_distance",
            "PULocationID": "pickup_location_id",
            "DOLocationID": "dropoff_location_id",
            "RatecodeID": "rate_code_id",
            "store_and_fwd_flag": "store_and_fwd_flag",
            "payment_type": "payment_type",
            "fare_amount": "fare_amount",
            "extra": "extra",
            "mta_tax": "mta_tax",
            "tip_amount": "tip_amount",
            "tolls_amount": "tolls_amount",
            "improvement_surcharge": "improvement_surcharge",
            "total_amount": "total_amount",
            "congestion_surcharge": "congestion_surcharge",
            "Airport_fee": "airport_fee",
        }

        df = df.rename(columns=column_mapping)

        # Remove invalid records
        df = df[df["fare_amount"] > 0]
        df = df[df["trip_distance"] > 0]
        df = df[df["passenger_count"] > 0]
        df = df[df["pickup_datetime"] < df["dropoff_datetime"]]

        # Handle nulls
        df = df.dropna(subset=["pickup_datetime", "dropoff_datetime", "vendor_id"])

        print(
            f"✓ Cleaned data: {initial_rows:,} → {len(df):,} rows ({initial_rows - len(df):,} removed)"
        )
        return df

    def load_to_postgres(self, df, batch_size=1000):
        """
        Load data into PostgreSQL using batch insert.

        Args:
            df (DataFrame): Cleaned data to load
            batch_size (int): Number of rows per batch
        """
        print(f"Loading {len(df):,} rows into PostgreSQL...")

        cursor = self.conn.cursor()

        # Prepare data
        columns = [
            "vendor_id",
            "pickup_datetime",
            "dropoff_datetime",
            "passenger_count",
            "trip_distance",
            "pickup_location_id",
            "dropoff_location_id",
            "rate_code_id",
            "store_and_fwd_flag",
            "payment_type",
            "fare_amount",
            "extra",
            "mta_tax",
            "tip_amount",
            "tolls_amount",
            "improvement_surcharge",
            "total_amount",
            "congestion_surcharge",
            "airport_fee",
        ]

        # Create insert query
        insert_query = f"""
            INSERT INTO rides ({", ".join(columns)})
            VALUES ({", ".join(["%s"] * len(columns))})
        """

        # Convert DataFrame to list of tuples
        data = [tuple(row) for row in df[columns].values]

        try:
            # Use execute_batch for better performance
            execute_batch(cursor, insert_query, data, page_size=batch_size)
            self.conn.commit()
            print(f"✓ Successfully loaded {len(data):,} rows")
        except Exception as e:
            self.conn.rollback()
            print(f"✗ Error loading data: {e}")
            raise
        finally:
            cursor.close()

    def run_etl(self, file_path, sample_size=None):
        """
        Run complete ETL pipeline.

        Args:
            file_path (str): Path to parquet file
            sample_size (int, optional): Number of rows to sample
        """
        start_time = datetime.now()
        print(f"\n{'=' * 60}")
        print(f"Starting ETL Pipeline - {start_time}")
        print(f"{'=' * 60}\n")

        if not self.connect():
            return

        try:
            # Load data
            df = self.load_parquet(file_path, sample_size)

            # Clean data
            df = self.clean_data(df)

            # Load to PostgreSQL
            self.load_to_postgres(df)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"\n{'=' * 60}")
            print(f"ETL Pipeline Completed - {end_time}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"{'=' * 60}\n")

        except Exception as e:
            print(f"✗ ETL pipeline failed: {e}")
        finally:
            if self.conn:
                self.conn.close()
                print("✓ Database connection closed")


if __name__ == "__main__":
    loader = TaxiDataLoader()

    # Start with a sample for testing
    file_path = "data/yellow_tripdata_2025-09.parquet"
    loader.run_etl(file_path, sample_size=100000)  # Start with 100k rows
