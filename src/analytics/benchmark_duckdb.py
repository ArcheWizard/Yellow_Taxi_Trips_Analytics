"""
Benchmark DuckDB with Parquet vs PostgreSQL Materialized Views.
Compares query performance and storage efficiency.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import duckdb
except ImportError:
    print("❌ DuckDB not installed. Install with: pip install duckdb")
    sys.exit(1)

from config.database import DatabaseConfig


class DuckDBBenchmark:
    """Benchmark DuckDB query performance on Parquet files."""

    def __init__(self, parquet_dir: str = "data/parquet"):
        """Initialize DuckDB connection with Parquet data."""
        self.parquet_dir = Path(parquet_dir)

        if not self.parquet_dir.exists():
            raise FileNotFoundError(
                f"Parquet directory not found: {self.parquet_dir}\n"
                "Run export_to_parquet.py first."
            )

        # Create in-memory DuckDB database
        self.conn = duckdb.connect(database=":memory:", read_only=False)

        # Register parquet files as views
        print("Loading Parquet files into DuckDB...")

        # Load rides (potentially multiple chunks)
        rides_files = list(self.parquet_dir.glob("rides_chunk_*.parquet"))
        if rides_files:
            files_str = "', '".join(str(f) for f in rides_files)
            self.conn.execute(
                f"CREATE VIEW rides AS SELECT * FROM read_parquet(['{files_str}']);"
            )
            print(f"  ✓ Loaded {len(rides_files)} rides chunk(s)")

        # Load zones
        zones_file = self.parquet_dir / "zones.parquet"
        if zones_file.exists():
            self.conn.execute(
                f"CREATE VIEW zones AS SELECT * FROM read_parquet('{zones_file}');"
            )
            print("  ✓ Loaded zones")

        print()

    def get_row_count(self) -> int:
        """Get total row count."""
        result = self.conn.execute("SELECT COUNT(*) FROM rides;").fetchone()
        return result[0]

    def benchmark_query(self, name: str, query: str, iterations: int = 3) -> dict:
        """Benchmark a single query."""
        times = []

        for _ in range(iterations):
            start = time.time()
            result = self.conn.execute(query).fetchall()
            duration = (time.time() - start) * 1000  # ms
            times.append(duration)

        return {
            "name": name,
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": sum(times) / len(times),
            "rows": len(result) if result else 0,
        }

    def run_analytics_queries(self) -> list:
        """Run standard analytics queries on DuckDB."""

        queries = [
            (
                "Hourly Stats",
                """
                SELECT
                    DATE_TRUNC('day', pickup_datetime) as date,
                    EXTRACT(HOUR FROM pickup_datetime) as hour,
                    COUNT(*) as trip_count,
                    ROUND(SUM(total_amount), 2) as total_revenue,
                    ROUND(AVG(total_amount), 2) as avg_fare
                FROM rides
                WHERE total_amount > 0
                GROUP BY date, hour
                ORDER BY date DESC, hour
                LIMIT 100;
            """,
            ),
            (
                "Top Pickup Locations",
                """
                SELECT
                    r.pickup_location_id,
                    z.zone,
                    COUNT(*) as pickup_count,
                    ROUND(AVG(r.total_amount), 2) as avg_fare
                FROM rides r
                LEFT JOIN zones z ON r.pickup_location_id = z.location_id
                WHERE r.total_amount > 0
                GROUP BY r.pickup_location_id, z.zone
                ORDER BY pickup_count DESC
                LIMIT 20;
            """,
            ),
            (
                "Popular Routes",
                """
                SELECT
                    r.pickup_location_id,
                    r.dropoff_location_id,
                    z_pickup.zone as pickup_zone,
                    z_dropoff.zone as dropoff_zone,
                    COUNT(*) as trip_count,
                    ROUND(AVG(r.total_amount), 2) as avg_fare
                FROM rides r
                LEFT JOIN zones z_pickup ON r.pickup_location_id = z_pickup.location_id
                LEFT JOIN zones z_dropoff ON r.dropoff_location_id = z_dropoff.location_id
                WHERE r.total_amount > 0
                GROUP BY r.pickup_location_id, r.dropoff_location_id,
                         z_pickup.zone, z_dropoff.zone
                HAVING COUNT(*) >= 10
                ORDER BY trip_count DESC
                LIMIT 20;
            """,
            ),
            (
                "Analytics Summary",
                """
                SELECT
                    COUNT(*) as total_trips,
                    ROUND(SUM(total_amount), 2) as total_revenue,
                    ROUND(AVG(total_amount), 2) as avg_fare,
                    ROUND(AVG(trip_distance), 2) as avg_distance
                FROM rides
                WHERE total_amount > 0;
            """,
            ),
            (
                "Time Patterns",
                """
                SELECT
                    EXTRACT(DOW FROM pickup_datetime) as day_of_week,
                    EXTRACT(HOUR FROM pickup_datetime) as hour,
                    COUNT(*) as trip_count,
                    ROUND(AVG(total_amount), 2) as avg_fare
                FROM rides
                WHERE total_amount > 0
                GROUP BY day_of_week, hour
                ORDER BY day_of_week, hour;
            """,
            ),
        ]

        results = []
        print("=" * 70)
        print("DUCKDB QUERY PERFORMANCE (on Parquet files)")
        print("=" * 70)

        for name, query in queries:
            result = self.benchmark_query(name, query)
            results.append(result)
            print(
                f"{result['name']:35} {result['avg_ms']:8.2f}ms  ({result['rows']} rows)"
            )

        print("=" * 70)
        print()

        return results

    def close(self):
        """Close DuckDB connection."""
        self.conn.close()


def benchmark_postgresql(db):
    """Benchmark PostgreSQL materialized views for comparison."""

    queries = [
        (
            "Hourly Stats (MV)",
            "SELECT * FROM mv_hourly_stats ORDER BY date DESC LIMIT 100;",
        ),
        (
            "Top Pickup Locations (MV)",
            "SELECT * FROM mv_top_pickup_locations ORDER BY pickup_count DESC LIMIT 20;",
        ),
        (
            "Popular Routes (MV)",
            "SELECT * FROM mv_popular_routes ORDER BY trip_count DESC LIMIT 20;",
        ),
        ("Analytics Summary (MV)", "SELECT * FROM mv_analytics_summary;"),
        (
            "Time Patterns (MV)",
            "SELECT * FROM mv_time_patterns ORDER BY day_of_week, hour;",
        ),
    ]

    conn = db.get_connection()
    try:
        cursor = conn.cursor()
        results = []

        print("=" * 70)
        print("POSTGRESQL MATERIALIZED VIEW PERFORMANCE")
        print("=" * 70)

        for name, query in queries:
            times = []
            rows = 0

            for _ in range(3):
                start = time.time()
                cursor.execute(query)
                result = cursor.fetchall()
                duration = (time.time() - start) * 1000
                times.append(duration)
                rows = len(result)

            avg_time = sum(times) / len(times)
            results.append({"name": name, "avg_ms": avg_time, "rows": rows})
            print(f"{name:35} {avg_time:8.2f}ms  ({rows} rows)")

        print("=" * 70)
        print()

        cursor.close()
        return results

    finally:
        db.return_connection(conn)


def compare_storage_size(parquet_dir: str):
    """Compare storage sizes between PostgreSQL and Parquet."""

    db = DatabaseConfig()
    conn = db.get_connection()

    try:
        cursor = conn.cursor()

        # Get PostgreSQL sizes
        cursor.execute("""
            SELECT
                pg_size_pretty(pg_total_relation_size('rides')) as rides_size,
                pg_size_pretty(SUM(pg_total_relation_size(matviewname::regclass))) as mv_total_size
            FROM pg_matviews
            WHERE schemaname = 'public';
        """)
        pg_rides_size, pg_mv_size = cursor.fetchone()

        # Get Parquet sizes
        parquet_path = Path(parquet_dir)
        if parquet_path.exists():
            parquet_size = sum(f.stat().st_size for f in parquet_path.glob("*.parquet"))
            parquet_size_mb = parquet_size / (1024**2)
        else:
            parquet_size_mb = 0

        print("=" * 70)
        print("STORAGE COMPARISON")
        print("=" * 70)
        print(f"PostgreSQL rides table:        {pg_rides_size}")
        print(f"PostgreSQL materialized views: {pg_mv_size}")
        print(f"Parquet files:                 {parquet_size_mb:.2f} MB")
        print("=" * 70)
        print()

        cursor.close()

    finally:
        db.return_connection(conn)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║          DuckDB + Parquet vs PostgreSQL Benchmark                    ║
║                                                                       ║
║  Compares:                                                           ║
║  • DuckDB query performance on Parquet files                         ║
║  • PostgreSQL materialized view performance                          ║
║  • Storage efficiency                                                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    parquet_dir = "data/parquet"

    # Check if parquet files exist
    if not Path(parquet_dir).exists():
        print("⚠️  Parquet files not found. Run export_to_parquet.py first:")
        print("    python src/analytics/export_to_parquet.py\n")
        return

    try:
        # Initialize DuckDB
        duckdb_bench = DuckDBBenchmark(parquet_dir)

        # Get dataset info
        row_count = duckdb_bench.get_row_count()
        print(f"Dataset: {row_count:,} rows\n")

        # Run DuckDB benchmarks
        duckdb_results = duckdb_bench.run_analytics_queries()

        # Run PostgreSQL benchmarks
        db = DatabaseConfig()
        pg_results = benchmark_postgresql(db)

        # Compare storage
        compare_storage_size(parquet_dir)

        # Summary comparison
        print("=" * 70)
        print("PERFORMANCE COMPARISON SUMMARY")
        print("=" * 70)
        print(f"{'Query Type':<35} {'DuckDB':>12} {'PostgreSQL':>12} {'Winner':>10}")
        print("-" * 70)

        for duck, pg in zip(duckdb_results, pg_results):
            duck_time = duck["avg_ms"]
            pg_time = pg["avg_ms"]
            winner = "DuckDB" if duck_time < pg_time else "PostgreSQL"
            speedup = max(duck_time, pg_time) / min(duck_time, pg_time)

            print(
                f"{duck['name']:<35} {duck_time:>10.2f}ms {pg_time:>10.2f}ms {winner:>10} ({speedup:.1f}x)"
            )

        print("=" * 70)

        # Overall winner
        duck_avg = sum(r["avg_ms"] for r in duckdb_results) / len(duckdb_results)
        pg_avg = sum(r["avg_ms"] for r in pg_results) / len(pg_results)

        print()
        print("Average Query Time:")
        print(f"  DuckDB (Parquet):            {duck_avg:.2f}ms")
        print(f"  PostgreSQL (Materialized):   {pg_avg:.2f}ms")

        if duck_avg < pg_avg:
            speedup = pg_avg / duck_avg
            print(f"  🏆 DuckDB is {speedup:.1f}x faster on average")
        else:
            speedup = duck_avg / pg_avg
            print(f"  🏆 PostgreSQL is {speedup:.1f}x faster on average")

        print()
        print("💡 Recommendations:")
        if duck_avg < pg_avg:
            print("  • DuckDB + Parquet is faster for analytical queries")
            print(
                "  • Consider hybrid approach: PostgreSQL for OLTP, DuckDB for analytics"
            )
            print("  • Parquet storage is more compact and faster to scan")
        else:
            print("  • PostgreSQL materialized views are faster (pre-computed)")
            print("  • Stick with current architecture for this dataset size")
            print("  • DuckDB may shine at larger scales (1M+ rows)")

        duckdb_bench.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
