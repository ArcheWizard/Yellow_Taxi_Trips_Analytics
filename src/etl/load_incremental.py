"""
Incremental data loading with benchmarking at 500K, 1M, and 3M row milestones.
Loads data month by month and runs comprehensive benchmarks at each target.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseConfig
from src.analytics.benchmark_incremental_refresh import (
    benchmark_full_refresh, benchmark_incremental_refresh, get_data_stats)
from src.analytics.benchmark_materialized_views import \
    MaterializedViewBenchmark
from src.etl.load_data import TaxiDataLoader


class IncrementalLoader:
    """Load data incrementally with benchmarking at milestones."""

    MILESTONES = [500_000, 1_000_000, 3_000_000]

    def __init__(self, data_dir: str = "data"):
        """Initialize incremental loader."""
        self.data_dir = Path(data_dir)
        self.db = DatabaseConfig()
        self.loader = TaxiDataLoader()
        self.current_rows = self.get_current_row_count()

        print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║         Incremental Data Loading & Benchmarking                      ║
║                                                                       ║
║  Current dataset: {self.current_rows:,} rows
║  Target milestones: 500K → 1M → 3M rows                              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)

    def get_current_row_count(self) -> int:
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

    def get_parquet_files(self):
        """Get list of parquet files sorted by date."""
        files = sorted(self.data_dir.glob("yellow_tripdata_*.parquet"))
        return files

    def load_until_milestone(self, target_rows: int):
        """Load data until we reach the target milestone."""
        print(f"\n{'=' * 70}")
        print(f"Loading data to reach {target_rows:,} rows...")
        print(f"Current: {self.current_rows:,} rows")
        print(f"Need: {target_rows - self.current_rows:,} more rows")
        print(f"{'=' * 70}\n")

        files = self.get_parquet_files()

        for file in files:
            if self.current_rows >= target_rows:
                print(f"\n✓ Target milestone reached: {self.current_rows:,} rows")
                break

            # Calculate how many more rows we need
            rows_needed = target_rows - self.current_rows

            print(f"Loading from: {file.name}")
            print(f"  Current: {self.current_rows:,} rows")
            print(f"  Need: {rows_needed:,} more rows")

            # Load with sample size if needed (add buffer to ensure we reach milestone)
            sample_size = rows_needed + 10000 if rows_needed < 3000000 else None

            try:
                # Use the existing TaxiDataLoader
                start_time = time.time()
                self.loader.run_etl(str(file), sample_size=sample_size)
                duration = time.time() - start_time

                # Update current count
                new_count = self.get_current_row_count()
                loaded = new_count - self.current_rows
                self.current_rows = new_count

                print(f"  ✓ Loaded {loaded:,} rows in {duration:.1f}s")
                print(f"  New total: {self.current_rows:,} rows")

                # Check if we've reached the milestone
                if self.current_rows >= target_rows:
                    print(f"\n✓✓✓ Milestone reached: {self.current_rows:,} rows ✓✓✓\n")
                    break

            except Exception as e:
                print(f"  ✗ Error loading {file.name}: {e}")
                continue

        return self.current_rows >= target_rows

    def run_benchmarks(self, milestone: int):
        """Run comprehensive benchmarks at current scale."""
        print(f"\n{'=' * 70}")
        print(f"BENCHMARKING AT {self.current_rows:,} ROWS")
        print(f"{'=' * 70}\n")

        # 1. Materialized view benchmarks
        print("Phase 1: Materialized View Performance...")
        mv_benchmark = MaterializedViewBenchmark()
        mv_results = mv_benchmark.benchmark_all_views(concurrent=True)
        query_results = mv_benchmark.benchmark_query_performance()
        raw_query_results = mv_benchmark.benchmark_raw_table_queries()

        # Combine results
        results = {
            **mv_results,
            "query_performance": query_results,
            "raw_query_performance": raw_query_results,
        }

        # Save results
        filename = f"benchmark_{milestone // 1000}K_rows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = mv_benchmark.save_results(results, filename)

        # Generate summary
        mv_benchmark.generate_summary_report(results)

        # 2. Incremental refresh benchmarks
        print("\nPhase 2: Incremental Refresh Performance...")

        # Get data distribution
        stats = get_data_stats(self.db)
        print("\nData Distribution:")
        print(f"  Total: {stats['total_rows']:,} rows")
        print(f"  Hot (30d): {stats['hot_rows']:,} rows ({stats['hot_pct']:.1f}%)")
        print(f"  Cold: {stats['cold_rows']:,} rows ({100 - stats['hot_pct']:.1f}%)")

        # Benchmark refresh strategies
        full_time = benchmark_full_refresh(self.db)
        hot_time = benchmark_incremental_refresh(self.db)

        speedup = full_time / hot_time if hot_time > 0 else 1

        print(f"\n{'=' * 70}")
        print("INCREMENTAL REFRESH SUMMARY")
        print(f"{'=' * 70}")
        print(f"Full Refresh:    {full_time:.3f}s")
        print(f"Hot Refresh:     {hot_time:.3f}s")
        print(f"Speedup:         {speedup:.1f}x faster")
        print(f"{'=' * 70}\n")

        return {
            "milestone": milestone,
            "row_count": self.current_rows,
            "mv_refresh_time": mv_results["total_refresh_time"],
            "full_refresh_time": full_time,
            "hot_refresh_time": hot_time,
            "speedup_factor": speedup,
            "query_avg_ms": sum(q["duration_ms"] for q in query_results)
            / len(query_results),
            "raw_query_avg_ms": sum(q["duration_ms"] for q in raw_query_results)
            / len(raw_query_results),
            "benchmark_file": str(filepath),
        }

    def refresh_materialized_views(self):
        """Refresh all materialized views after loading."""
        print(f"\n{'=' * 70}")
        print("Refreshing Materialized Views...")
        print(f"{'=' * 70}\n")

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()

            # Refresh incremental views
            try:
                cursor.execute("SELECT refresh_all_incremental_mv();")
                conn.commit()
                print("✓ Incremental views refreshed")
            except Exception as e:
                print(f"⚠️  Incremental refresh not available: {e}")
                print("   Falling back to standard refresh...")

                # Fallback to standard refresh
                standard_views = [
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

                for view in standard_views:
                    try:
                        cursor.execute(
                            f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};"
                        )
                        conn.commit()
                        print(f"  ✓ {view}")
                    except Exception as ve:
                        print(f"  ✗ {view}: {ve}")

            print("\n✓ All materialized views refreshed\n")
            cursor.close()
        finally:
            self.db.return_connection(conn)

    def run(self):
        """Run the complete incremental loading and benchmarking process."""
        results_summary = []

        for milestone in self.MILESTONES:
            if self.current_rows >= milestone:
                print(
                    f"\n✓ Milestone {milestone:,} already reached ({self.current_rows:,} rows)"
                )
                continue

            # Load data to milestone
            print(f"\n\n{'#' * 70}")
            print(f"# MILESTONE: {milestone:,} ROWS")
            print(f"{'#' * 70}\n")

            success = self.load_until_milestone(milestone)

            if not success:
                print(f"\n✗ Failed to reach milestone {milestone:,} rows")
                print(f"Current: {self.current_rows:,} rows")
                break

            # Refresh materialized views
            self.refresh_materialized_views()

            # Run benchmarks
            benchmark_results = self.run_benchmarks(milestone)
            results_summary.append(benchmark_results)

            # Summary
            print(f"\n{'=' * 70}")
            print(f"MILESTONE {milestone:,} COMPLETE")
            print(f"{'=' * 70}")
            print(f"Actual rows: {self.current_rows:,}")
            print(f"MV refresh: {benchmark_results['mv_refresh_time']:.2f}s")
            print(
                f"Hot refresh: {benchmark_results['hot_refresh_time']:.3f}s ({benchmark_results['speedup_factor']:.1f}x speedup)"
            )
            print(f"Query avg: {benchmark_results['query_avg_ms']:.2f}ms")
            print(f"{'=' * 70}\n")

        # Final summary
        print(f"\n\n{'#' * 70}")
        print("# SCALING TEST COMPLETE")
        print(f"{'#' * 70}\n")

        print("Results Summary:")
        print(
            f"{'Milestone':<12} {'Rows':<12} {'MV Refresh':<15} {'Hot Refresh':<15} {'Speedup':<10}"
        )
        print("-" * 70)

        for result in results_summary:
            print(
                f"{result['milestone'] // 1000}K rows      "
                f"{result['row_count']:>10,}  "
                f"{result['mv_refresh_time']:>12.2f}s  "
                f"{result['hot_refresh_time']:>12.3f}s  "
                f"{result['speedup_factor']:>8.1f}x"
            )

        # Save summary
        summary_file = (
            f"logs/scaling_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        Path("logs").mkdir(exist_ok=True)
        with open(summary_file, "w") as f:
            json.dump(results_summary, f, indent=2)
        print(f"\n✓ Summary saved to: {summary_file}")

        print("\n✓ All scaling tests complete!")
        print("\nNext steps:")
        print("1. Review benchmark results in logs/ directory")
        print("2. Analyze scaling behavior (linear vs sub-linear)")
        print("3. Update documentation with findings")
        print("4. Create Metabase dashboards with full dataset\n")


def main():
    """Run incremental loading and benchmarking."""
    loader = IncrementalLoader()
    loader.run()


if __name__ == "__main__":
    main()
