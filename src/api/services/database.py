"""
Database service layer for API operations.
Handles all database queries and connections.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from config.database import DatabaseConfig

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service class for database operations."""

    def __init__(self):
        """Initialize database service with configuration."""
        self.config = DatabaseConfig()

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        conn = None
        try:
            conn = self.config.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.config.return_connection(conn)
                return True
            return False
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_rides(
        self,
        limit: int = 100,
        offset: int = 0,
        vendor_id: Optional[int] = None,
        payment_type: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated list of rides with optional filters.

        Args:
            limit: Number of records to return
            offset: Number of records to skip
            vendor_id: Filter by vendor ID
            payment_type: Filter by payment type
            date_from: Filter rides from this date
            date_to: Filter rides until this date

        Returns:
            Dictionary with 'data' (list of rides) and 'total' (total count)
        """
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = []
            params = []

            if vendor_id:
                where_conditions.append("vendor_id = %s")
                params.append(vendor_id)

            if payment_type:
                where_conditions.append("payment_type = %s")
                params.append(payment_type)

            if date_from:
                where_conditions.append("pickup_datetime >= %s")
                params.append(date_from)

            if date_to:
                where_conditions.append("pickup_datetime <= %s")
                params.append(date_to)

            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM rides {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            # Get paginated data
            query = f"""
                SELECT
                    ride_id, vendor_id, pickup_datetime, dropoff_datetime,
                    passenger_count, trip_distance, pickup_location_id,
                    dropoff_location_id, rate_code_id, store_and_fwd_flag,
                    payment_type, fare_amount, extra, mta_tax, tip_amount,
                    tolls_amount, improvement_surcharge, total_amount,
                    congestion_surcharge, airport_fee, created_at
                FROM rides
                {where_clause}
                ORDER BY pickup_datetime DESC
                LIMIT %s OFFSET %s
            """

            cursor.execute(query, params + [limit, offset])
            columns = [desc[0] for desc in cursor.description]
            rides = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return {"data": rides, "total": total}

        except Exception as e:
            logger.error(f"Error fetching rides: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_ride_by_id(self, ride_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single ride by ID.

        Args:
            ride_id: The ride ID to fetch

        Returns:
            Dictionary with ride data or None if not found
        """
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    ride_id, vendor_id, pickup_datetime, dropoff_datetime,
                    passenger_count, trip_distance, pickup_location_id,
                    dropoff_location_id, rate_code_id, store_and_fwd_flag,
                    payment_type, fare_amount, extra, mta_tax, tip_amount,
                    tolls_amount, improvement_surcharge, total_amount,
                    congestion_surcharge, airport_fee, created_at
                FROM rides
                WHERE ride_id = %s
            """

            cursor.execute(query, (ride_id,))
            row = cursor.fetchone()

            if row:
                columns = [desc[0] for desc in cursor.description]
                result = dict(zip(columns, row))
            else:
                result = None

            cursor.close()

            return result

        except Exception as e:
            logger.error(f"Error fetching ride {ride_id}: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_analytics_summary(
        self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get overall analytics summary.
        Uses materialized view for fast queries when no date filters are applied.

        Args:
            date_from: Start date for analysis
            date_to: End date for analysis

        Returns:
            Dictionary with summary statistics
        """
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            # If no date filters, use materialized view (FAST!)
            if not date_from and not date_to:
                query = """
                    SELECT
                        total_trips,
                        total_revenue,
                        avg_fare,
                        avg_distance,
                        avg_duration_min,
                        date_range_start,
                        date_range_end
                    FROM mv_analytics_summary
                """
                cursor.execute(query)
            else:
                # Use original query with date filters
                where_conditions = [
                    "total_amount > 0",
                    "dropoff_datetime > pickup_datetime",
                ]
                params = []

                if date_from:
                    where_conditions.append("pickup_datetime >= %s")
                    params.append(date_from)

                if date_to:
                    where_conditions.append("pickup_datetime <= %s")
                    params.append(date_to)

                where_clause = "WHERE " + " AND ".join(where_conditions)

                query = f"""
                    SELECT
                        COUNT(*) as total_trips,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as avg_fare,
                        AVG(trip_distance) as avg_distance,
                        AVG(EXTRACT(EPOCH FROM (dropoff_datetime - pickup_datetime))/60) as avg_duration_min,
                        MIN(pickup_datetime) as date_range_start,
                        MAX(pickup_datetime) as date_range_end
                    FROM rides
                    {where_clause}
                """

                cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, cursor.fetchone()))

            cursor.close()

            return result

        except Exception as e:
            logger.error(f"Error fetching analytics summary: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_hourly_stats(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get hourly statistics from incremental materialized view (hot + cold partitions)."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    date, hour, trip_count, total_revenue,
                    avg_distance, avg_fare, avg_duration_min,
                    credit_card_count, cash_count
                FROM mv_hourly_stats_incremental
                ORDER BY date DESC, hour DESC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching hourly stats: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_top_pickup_locations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top pickup locations from incremental materialized view (hot + cold partitions)."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    pickup_location_id as location_id, borough, zone, pickup_count as trip_count,
                    avg_distance, avg_fare, total_revenue / NULLIF(pickup_count, 0) as avg_tip, pct_of_total
                FROM mv_top_pickup_locations_incremental
                WHERE zone IS NOT NULL
                ORDER BY pickup_count DESC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching top pickup locations: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_top_dropoff_locations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top dropoff locations from materialized view."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    dropoff_location_id as location_id, borough, zone, dropoff_count,
                    avg_distance, avg_fare, total_revenue / NULLIF(dropoff_count, 0) as avg_tip, pct_of_total
                FROM mv_top_dropoff_locations
                WHERE zone IS NOT NULL
                ORDER BY dropoff_count DESC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching top dropoff locations: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_vendor_performance(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get vendor daily performance from materialized view."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    vendor_id, vendor_name, date, trip_count,
                    total_revenue, avg_fare, avg_distance as avg_trip_distance
                FROM mv_vendor_daily_performance
                ORDER BY date DESC, vendor_id
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching vendor performance: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_payment_hourly_stats(self) -> List[Dict[str, Any]]:
        """Get payment type hourly statistics from materialized view."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    hour, payment_type, trip_count,
                    total_revenue as total_amount, avg_fare as avg_amount
                FROM mv_payment_hourly
                ORDER BY hour, payment_type
            """

            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching payment hourly stats: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_distance_segments(self) -> List[Dict[str, Any]]:
        """Get distance segment statistics from materialized view."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    distance_segment as segment, trip_count, avg_fare,
                    median_fare as avg_tip, pct_of_total
                FROM mv_distance_segments
                ORDER BY
                    CASE distance_segment
                        WHEN '0-2 miles' THEN 1
                        WHEN '2-5 miles' THEN 2
                        WHEN '5-10 miles' THEN 3
                        WHEN '10-20 miles' THEN 4
                        WHEN '20+ miles' THEN 5
                    END
            """

            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching distance segments: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_time_patterns(self, limit: int = 168) -> List[Dict[str, Any]]:
        """Get time patterns from materialized view."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    day_of_week, hour, trip_count,
                    avg_fare, avg_distance
                FROM mv_time_patterns
                ORDER BY day_of_week, hour
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching time patterns: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)

    def get_popular_routes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular routes from incremental materialized view (hot + cold partitions)."""
        conn = None
        try:
            conn = self.config.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    pickup_location_id, dropoff_location_id,
                    pickup_zone, dropoff_zone, trip_count,
                    avg_fare, avg_distance, avg_duration_min
                FROM mv_popular_routes_incremental
                WHERE pickup_zone IS NOT NULL AND dropoff_zone IS NOT NULL
                ORDER BY trip_count DESC
                LIMIT %s
            """

            cursor.execute(query, (limit,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            cursor.close()

            return results

        except Exception as e:
            logger.error(f"Error fetching popular routes: {e}")
            raise
        finally:
            if conn:
                self.config.return_connection(conn)


# Singleton instance
db_service = DatabaseService()
