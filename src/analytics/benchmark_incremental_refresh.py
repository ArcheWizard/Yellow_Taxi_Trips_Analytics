"""
Benchmark incremental refresh strategy vs full refresh.
Compares hot/cold partitioning performance benefits.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.database import DatabaseConfig

def benchmark_full_refresh(db):
    """Benchmark traditional full refresh approach."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        views = ['mv_hourly_stats', 'mv_top_pickup_locations', 'mv_popular_routes']
        times = []

        print("\n" + "="*70)
        print("FULL REFRESH APPROACH (Traditional)")
        print("="*70)

        for view in views:
            start = time.time()
            cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};")
            conn.commit()
            duration = time.time() - start
            times.append(duration)
            print(f"{view:40} {duration:8.3f}s")

        total = sum(times)
        print(f"{'TOTAL':40} {total:8.3f}s")
        print("="*70)

        cursor.close()
        return total

    finally:
        db.return_connection(conn)

def benchmark_incremental_refresh(db):
    """Benchmark incremental hot-only refresh approach."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        print("\n" + "="*70)
        print("INCREMENTAL REFRESH APPROACH (Hot Data Only)")
        print("="*70)

        start = time.time()
        cursor.execute("SELECT refresh_hot_mv();")
        conn.commit()
        duration = time.time() - start

        print(f"{'refresh_hot_mv() - all 3 hot views':40} {duration:8.3f}s")
        print("="*70)

        cursor.close()
        return duration

    finally:
        db.return_connection(conn)

def benchmark_cold_refresh(db):
    """Benchmark cold data refresh (infrequent operation)."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        print("\n" + "="*70)
        print("COLD REFRESH (Historical Data - Weekly)")
        print("="*70)

        start = time.time()
        cursor.execute("SELECT refresh_cold_mv();")
        conn.commit()
        duration = time.time() - start

        print(f"{'refresh_cold_mv() - all 3 cold views':40} {duration:8.3f}s")
        print("="*70)

        cursor.close()
        return duration

    finally:
        db.return_connection(conn)

def get_data_stats(db):
    """Get statistics about hot vs cold data distribution."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        # Total rows
        cursor.execute("SELECT COUNT(*) FROM rides;")
        total_rows = cursor.fetchone()[0]

        # Hot data rows (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) FROM rides
            WHERE pickup_datetime >= CURRENT_DATE - INTERVAL '30 days';
        """)
        hot_rows = cursor.fetchone()[0]

        cold_rows = total_rows - hot_rows
        hot_pct = (hot_rows / total_rows * 100) if total_rows > 0 else 0

        # View sizes
        cursor.execute("""
            SELECT
                pg_size_pretty(pg_total_relation_size('mv_hourly_stats')) as full_size,
                pg_size_pretty(pg_total_relation_size('mv_hourly_stats_hot')) as hot_size,
                pg_size_pretty(pg_total_relation_size('mv_hourly_stats_cold')) as cold_size;
        """)
        sizes = cursor.fetchone()

        cursor.close()
        return {
            'total_rows': total_rows,
            'hot_rows': hot_rows,
            'cold_rows': cold_rows,
            'hot_pct': hot_pct,
            'full_size': sizes[0],
            'hot_size': sizes[1],
            'cold_size': sizes[2]
        }

    finally:
        db.return_connection(conn)

def compare_query_performance(db):
    """Compare query performance between old and new views."""
    conn = db.get_connection()
    try:
        cursor = conn.cursor()

        print("\n" + "="*70)
        print("QUERY PERFORMANCE COMPARISON")
        print("="*70)

        queries = [
            ("Old: mv_hourly_stats", "SELECT * FROM mv_hourly_stats ORDER BY date DESC LIMIT 100;"),
            ("New: mv_hourly_stats_incremental", "SELECT * FROM mv_hourly_stats_incremental LIMIT 100;"),
            ("Old: mv_top_pickup_locations", "SELECT * FROM mv_top_pickup_locations ORDER BY pickup_count DESC LIMIT 20;"),
            ("New: mv_top_pickup_locations_incremental", "SELECT * FROM mv_top_pickup_locations_incremental LIMIT 20;"),
        ]

        for name, query in queries:
            times = []
            for _ in range(3):
                start = time.time()
                cursor.execute(query)
                cursor.fetchall()
                times.append((time.time() - start) * 1000)

            avg_time = sum(times) / len(times)
            print(f"{name:45} {avg_time:6.2f}ms")

        print("="*70)
        cursor.close()

    finally:
        db.return_connection(conn)

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║       Incremental Refresh Strategy Benchmark                         ║
║                                                                       ║
║  Compares:                                                           ║
║  • Full refresh (all data)                                           ║
║  • Hot refresh (last 30 days only)                                   ║
║  • Query performance (old vs new views)                              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    db = DatabaseConfig()

    # Get data distribution
    print("\n" + "="*70)
    print("DATA DISTRIBUTION")
    print("="*70)
    stats = get_data_stats(db)
    print(f"Total Rows:        {stats['total_rows']:,}")
    print(f"Hot Rows (30d):    {stats['hot_rows']:,} ({stats['hot_pct']:.1f}%)")
    print(f"Cold Rows:         {stats['cold_rows']:,} ({100-stats['hot_pct']:.1f}%)")
    print()
    print(f"Full View Size:    {stats['full_size']}")
    print(f"Hot View Size:     {stats['hot_size']}")
    print(f"Cold View Size:    {stats['cold_size']}")
    print("="*70)

    # Benchmark refreshes
    try:
        full_time = benchmark_full_refresh(db)
        hot_time = benchmark_incremental_refresh(db)
        cold_time = benchmark_cold_refresh(db)

        # Calculate speedup
        speedup = full_time / hot_time if hot_time > 0 else 1

        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY")
        print("="*70)
        print(f"Full Refresh Time:        {full_time:.3f}s")
        print(f"Hot Refresh Time:         {hot_time:.3f}s")
        print(f"Cold Refresh Time:        {cold_time:.3f}s")
        print(f"Speedup Factor:           {speedup:.1f}x faster")
        print()
        print("Recommendation:")
        if speedup >= 5:
            print("  ✅ Use incremental refresh - significant performance gain!")
        elif speedup >= 2:
            print("  ⚠️  Use incremental refresh - moderate performance gain")
        else:
            print("  ℹ️  Dataset too small - full refresh is acceptable")
        print("="*70)

        # Compare query performance
        compare_query_performance(db)

        # Scaling predictions
        print("\n" + "="*70)
        print("SCALING PREDICTIONS")
        print("="*70)
        print("Dataset    | Full Refresh | Hot Refresh | Speedup")
        print("-----------|--------------|-------------|--------")
        print(f"93K rows   |    {full_time:.2f}s      |    {hot_time:.2f}s     |  {speedup:.1f}x")

        # Extrapolate based on current ratio
        if stats['hot_rows'] > 0:
            for target_rows in [500000, 1000000, 3000000, 10000000]:
                estimated_full = full_time * (target_rows / stats['total_rows'])
                # Hot time stays relatively constant (30-day window)
                estimated_hot = hot_time * 1.2  # Slight increase
                estimated_speedup = estimated_full / estimated_hot
                print(f"{target_rows//1000}K rows  |    {estimated_full:5.1f}s     |    {estimated_hot:.2f}s     | {estimated_speedup:5.1f}x")

        print("="*70)
        print()
        print("💡 Key Insight:")
        print("   As dataset grows, hot refresh time stays constant while")
        print("   full refresh time increases linearly with data size.")
        print()

    except Exception as e:
        print(f"❌ Error during benchmark: {e}")
        raise

if __name__ == "__main__":
    main()
