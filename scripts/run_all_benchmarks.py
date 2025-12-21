"""
Run comprehensive benchmarks on the full dataset (17.4M rows).
This will measure:
1. Materialized view refresh times
2. Incremental (hot/cold) refresh performance
3. Query performance on materialized views vs raw table
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_benchmark(script_path: str, description: str):
    """Run a benchmark script and display results."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}\n")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✓ {description} completed successfully\n")
        else:
            print(f"\n✗ {description} failed with return code {result.returncode}\n")

    except Exception as e:
        print(f"\n✗ Error running {description}: {e}\n")

def main():
    print(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║         Comprehensive Benchmark Suite - 17.4M Rows                   ║
║                                                                       ║
║  This will run all performance benchmarks on the full dataset        ║
║  Estimated time: 5-10 minutes                                        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    benchmarks = [
        ("src/analytics/benchmark_materialized_views.py", "Materialized View Benchmark"),
        ("src/analytics/benchmark_incremental_refresh.py", "Incremental Refresh Benchmark"),
    ]

    for script_path, description in benchmarks:
        run_benchmark(script_path, description)

    print(f"\n{'='*70}")
    print("ALL BENCHMARKS COMPLETE")
    print(f"{'='*70}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nResults saved in logs/ directory")
    print("Review the following files:")
    print("  - logs/benchmark_17417027_rows_*.json")
    print("  - Terminal output above")
    print("\nNext steps:")
    print("  1. Analyze scaling behavior (refresh times at 17M vs 93K)")
    print("  2. Update documentation with findings")
    print("  3. Create Metabase dashboards with full dataset")
    print()

if __name__ == "__main__":
    main()