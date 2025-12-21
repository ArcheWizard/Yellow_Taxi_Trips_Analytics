"""
Benchmark materialized view refresh times and query performance at scale.
Tests system behavior at various dataset sizes (93K, 500K, 1M, 3M rows).

This script helps identify performance bottlenecks and scaling limits.
"""

import json
import logging
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MaterializedViewBenchmark:
    """Benchmark materialized views at different scales."""

    VIEWS = [
        "mv_hourly_stats",
        "mv_top_pickup_locations",
        "mv_top_dropoff_locations",
        "mv_vendor_daily_performance",
        "mv_payment_hourly",
        "mv_distance_segments",
        "mv_time_patterns",
        "mv_popular_routes",
        "mv_analytics_summary",
    ]

    def __init__(self):
        """Initialize benchmark with database configuration."""
        self.db = DatabaseConfig()
        logger.info("MaterializedViewBenchmark initialized")

    def get_row_count(self) -> int:
        """Get current row count in rides table."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rides;")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        finally:
            self.db.return_connection(conn)

    def get_table_size(self, table_name: str) -> tuple:
        """Get table size in human-readable format."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT
                    pg_size_pretty(pg_total_relation_size('{table_name}')) as size,
                    pg_total_relation_size('{table_name}') as bytes
            """)
            result = cursor.fetchone()
            cursor.close()
            return result[0], result[1]
        finally:
            self.db.return_connection(conn)

    def benchmark_view_refresh(self, view_name: str, concurrent: bool = True) -> Dict:
        """
        Benchmark refresh time for a single materialized view.

        Args:
            view_name: Name of the materialized view
            concurrent: Use CONCURRENTLY option (default: True)

        Returns:
            Dictionary with benchmark results
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # Get view size before refresh
            size_before, bytes_before = self.get_table_size(view_name)

            # Measure refresh time
            refresh_cmd = f"REFRESH MATERIALIZED VIEW {'CONCURRENTLY' if concurrent else ''} {view_name}"
            logger.debug(f"Executing: {refresh_cmd}")

            start = time.time()
            cursor.execute(refresh_cmd)
            conn.commit()
            duration = time.time() - start

            # Get view size after refresh
            size_after, bytes_after = self.get_table_size(view_name)

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {view_name};")
            row_count = cursor.fetchone()[0]

            cursor.close()

            return {
                "view": view_name,
                "duration_seconds": round(duration, 3),
                "size_human": size_after,
                "size_bytes": bytes_after,
                "rows": row_count,
                "concurrent": concurrent,
            }
        finally:
            self.db.return_connection(conn)

    def benchmark_all_views(self, concurrent: bool = True) -> Dict:
        """
        Benchmark all materialized views.

        Args:
            concurrent: Use CONCURRENTLY option for all refreshes

        Returns:
            Dictionary with complete benchmark results
        """
        row_count = self.get_row_count()
        rides_size, rides_bytes = self.get_table_size("rides")

        print(f"\n{'=' * 70}")
        print(f"Benchmarking Materialized Views at {row_count:,} rows")
        print(f"{'=' * 70}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Base table size: {rides_size}")
        print(f"Concurrent refresh: {concurrent}")
        print(f"{'=' * 70}\n")

        results = []
        total_time = 0
        total_view_size = 0

        for view in self.VIEWS:
            print(f"Refreshing {view:40s}... ", end="", flush=True)

            try:
                result = self.benchmark_view_refresh(view, concurrent=concurrent)
                results.append(result)
                total_time += result["duration_seconds"]
                total_view_size += result["size_bytes"]

                print(
                    f"{result['duration_seconds']:6.3f}s  ({result['size_human']:>8s}, {result['rows']:>6,} rows)"
                )

            except Exception as e:
                logger.error(f"Error refreshing {view}: {e}")
                print(f"FAILED: {e}")
                results.append({"view": view, "error": str(e), "duration_seconds": 0})

        print(f"\n{'=' * 70}")
        print(f"TOTAL REFRESH TIME: {total_time:.2f} seconds")
        print(f"TOTAL VIEW SIZE:    {self._format_bytes(total_view_size)}")
        print(
            f"AVG REFRESH TIME:   {total_time / len(self.VIEWS):.2f} seconds per view"
        )
        print(f"{'=' * 70}\n")

        return {
            "timestamp": datetime.now().isoformat(),
            "row_count": row_count,
            "rides_size_bytes": rides_bytes,
            "rides_size_human": rides_size,
            "total_refresh_time": round(total_time, 2),
            "total_view_size_bytes": total_view_size,
            "total_view_size_human": self._format_bytes(total_view_size),
            "avg_refresh_time": round(total_time / len(self.VIEWS), 2),
            "concurrent": concurrent,
            "views": results,
        }

    def benchmark_query_performance(self) -> List[Dict]:
        """
        Benchmark query performance on materialized views.

        Returns:
            List of query benchmark results
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            queries = [
                ("Hourly Stats (100 rows)", "SELECT * FROM mv_hourly_stats LIMIT 100"),
                (
                    "Top 20 Pickup Locations",
                    "SELECT * FROM mv_top_pickup_locations LIMIT 20",
                ),
                (
                    "Top 20 Dropoff Locations",
                    "SELECT * FROM mv_top_dropoff_locations LIMIT 20",
                ),
                (
                    "Popular Routes (20 routes)",
                    "SELECT * FROM mv_popular_routes LIMIT 20",
                ),
                ("Analytics Summary", "SELECT * FROM mv_analytics_summary"),
                (
                    "Time Patterns (168 rows)",
                    "SELECT * FROM mv_time_patterns LIMIT 168",
                ),
                ("Distance Segments", "SELECT * FROM mv_distance_segments"),
                ("Payment Hourly Stats", "SELECT * FROM mv_payment_hourly LIMIT 100"),
                (
                    "Vendor Performance",
                    "SELECT * FROM mv_vendor_daily_performance LIMIT 30",
                ),
            ]

            print(f"\n{'=' * 70}")
            print("Query Performance on Materialized Views")
            print(f"{'=' * 70}\n")

            results = []
            for query_name, query in queries:
                # Run query 3 times and take average
                times = []
                for _ in range(3):
                    start = time.time()
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    duration = (time.time() - start) * 1000  # Convert to ms
                    times.append(duration)

                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)

                results.append(
                    {
                        "query": query_name,
                        "duration_ms": round(avg_time, 2),
                        "min_ms": round(min_time, 2),
                        "max_ms": round(max_time, 2),
                        "rows_returned": len(rows),
                    }
                )

                print(
                    f"{query_name:40s}: {avg_time:6.2f}ms  (min: {min_time:.2f}ms, max: {max_time:.2f}ms, {len(rows)} rows)"
                )

            cursor.close()
            print(f"\n{'=' * 70}\n")

            return results
        finally:
            self.db.return_connection(conn)

    def benchmark_raw_table_queries(self) -> List[Dict]:
        """
        Benchmark queries on the raw rides table (without materialized views).
        This helps understand the performance gain from using materialized views.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            queries = [
                (
                    "Raw: Hourly aggregation",
                    """
                    SELECT
                        DATE(pickup_datetime) as date,
                        EXTRACT(HOUR FROM pickup_datetime)::int as hour,
                        COUNT(*) as trip_count
                    FROM rides
                    GROUP BY date, hour
                    ORDER BY date DESC, hour
                    LIMIT 100
                """,
                ),
                (
                    "Raw: Top pickup locations",
                    """
                    SELECT
                        pickup_location_id,
                        COUNT(*) as pickup_count
                    FROM rides
                    GROUP BY pickup_location_id
                    ORDER BY pickup_count DESC
                    LIMIT 20
                """,
                ),
                (
                    "Raw: Popular routes",
                    """
                    SELECT
                        pickup_location_id,
                        dropoff_location_id,
                        COUNT(*) as trip_count
                    FROM rides
                    WHERE pickup_location_id != dropoff_location_id
                    GROUP BY pickup_location_id, dropoff_location_id
                    ORDER BY trip_count DESC
                    LIMIT 20
                """,
                ),
            ]

            print(f"\n{'=' * 70}")
            print("Raw Table Query Performance (without materialized views)")
            print(f"{'=' * 70}\n")

            results = []
            for query_name, query in queries:
                start = time.time()
                cursor.execute(query)
                rows = cursor.fetchall()
                duration = (time.time() - start) * 1000  # Convert to ms

                results.append(
                    {
                        "query": query_name,
                        "duration_ms": round(duration, 2),
                        "rows_returned": len(rows),
                    }
                )

                print(f"{query_name:40s}: {duration:6.2f}ms ({len(rows)} rows)")

            cursor.close()
            print(f"\n{'=' * 70}\n")

            return results
        finally:
            self.db.return_connection(conn)

    def save_results(self, results: Dict, filename: str = None):
        """
        Save benchmark results to JSON file.

        Args:
            results: Benchmark results dictionary
            filename: Optional custom filename
        """
        if not filename:
            filename = f"benchmark_{results['row_count']}_rows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Ensure logs directory exists
        logs_dir = project_root / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)

        filepath = logs_dir / filename

        # Ensure filepath is a file path, not a directory
        if filepath.is_dir():
            raise ValueError(f"Expected file path but got directory: {filepath}")

        with open(str(filepath), "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to: {filepath}")
        print(f"\n✓ Results saved to: {filepath}\n")

        return filepath

    @staticmethod
    def _format_bytes(bytes_size: float) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    def generate_summary_report(self, results: Dict):
        """Generate a human-readable summary report."""
        print(f"\n{'=' * 70}")
        print("BENCHMARK SUMMARY")
        print(f"{'=' * 70}")
        print(
            f"Dataset Size:           {results['row_count']:,} rows ({results['rides_size_human']})"
        )
        print(f"Total Views:            {len(results['views'])} materialized views")
        print(f"Total View Size:        {results['total_view_size_human']}")
        print(f"Total Refresh Time:     {results['total_refresh_time']:.2f} seconds")
        print(
            f"Average Refresh Time:   {results['avg_refresh_time']:.2f} seconds per view"
        )

        if "query_performance" in results:
            avg_query_time = statistics.mean(
                [q["duration_ms"] for q in results["query_performance"]]
            )
            print(f"Avg Query Time (MV):    {avg_query_time:.2f}ms")

        if "raw_query_performance" in results:
            avg_raw_time = statistics.mean(
                [q["duration_ms"] for q in results["raw_query_performance"]]
            )
            print(f"Avg Query Time (Raw):   {avg_raw_time:.2f}ms")

            if "query_performance" in results:
                mv_avg = statistics.mean(
                    [q["duration_ms"] for q in results["query_performance"]]
                )
                speedup = avg_raw_time / mv_avg
                print(
                    f"Speedup Factor:         {speedup:.1f}x faster with materialized views"
                )

        print(f"{'=' * 70}\n")

        # Identify slowest views
        print("Slowest Materialized Views:")
        sorted_views = sorted(
            results["views"], key=lambda x: x.get("duration_seconds", 0), reverse=True
        )
        for i, view in enumerate(sorted_views[:3], 1):
            if "error" not in view:
                print(
                    f"  {i}. {view['view']:35s} {view['duration_seconds']:6.3f}s ({view['size_human']})"
                )

        print()


def main():
    """Run complete benchmark suite."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║         Materialized View Performance Benchmark Suite                ║
║                                                                       ║
║  This benchmark measures:                                            ║
║  • Materialized view refresh times at current scale                  ║
║  • Query performance on materialized views                           ║
║  • Raw table query performance (for comparison)                      ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    benchmark = MaterializedViewBenchmark()

    # Run benchmarks
    try:
        # 1. Benchmark refresh times
        print("Phase 1: Benchmarking materialized view refresh times...")
        refresh_results = benchmark.benchmark_all_views(concurrent=True)

        # 2. Benchmark query performance on materialized views
        print("Phase 2: Benchmarking query performance...")
        query_results = benchmark.benchmark_query_performance()

        # 3. Benchmark raw table queries (for comparison)
        print("Phase 3: Benchmarking raw table queries...")
        raw_query_results = benchmark.benchmark_raw_table_queries()

        # Combine results
        results = {
            **refresh_results,
            "query_performance": query_results,
            "raw_query_performance": raw_query_results,
        }

        # Save results
        filepath = benchmark.save_results(results)

        # Generate summary
        benchmark.generate_summary_report(results)

        print(f"✓ Benchmark complete! Results saved to: {filepath}")

        return results

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
