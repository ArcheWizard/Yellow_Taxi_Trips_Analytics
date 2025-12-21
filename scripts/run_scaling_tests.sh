#!/bin/bash
#
# Run scaling tests: download data and load incrementally to 500K, 1M, 3M milestones
#

set -e

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║              Scaling Tests for Yellow Taxi Analytics                 ║"
echo "║                                                                       ║"
echo "║  Phase 1: Download additional data (~5-10 min)                       ║"
echo "║  Phase 2: Load and benchmark at 500K, 1M, 3M rows (~25-30 min)       ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Phase 1: Download data
echo "Phase 1: Downloading additional data..."
echo "========================================"
bash scripts/download_additional_data.sh
echo
echo "✓ Data download complete"
echo

# Phase 2: Run incremental loading
echo "Phase 2: Running incremental loading with benchmarks..."
echo "========================================================"
python src/etl/load_incremental.py

echo
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║                   ✓ Scaling Tests Complete!                          ║"
echo "║                                                                       ║"
echo "║  Check logs/ directory for detailed benchmark results                ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
