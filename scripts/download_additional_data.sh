#!/bin/bash
# Download additional months of NYC taxi data for scaling tests

DATA_DIR="data"
BASE_URL="https://d37ci6vzurychx.cloudfront.net/trip-data"

echo "========================================="
echo "Downloading Additional NYC Taxi Data"
echo "========================================="
echo ""

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Download 2025 data (July, August, October, November)
# Each month has approximately 3M rows
MONTHS=("2025-07" "2025-08" "2025-10" "2025-11")

for month in "${MONTHS[@]}"; do
    filename="yellow_tripdata_${month}.parquet"
    url="${BASE_URL}/${filename}"
    output="${DATA_DIR}/${filename}"

    if [ -f "$output" ]; then
        echo "✓ $filename already exists, skipping"
    else
        echo "Downloading $filename..."
        wget -q --show-progress "$url" -O "$output"

        if [ $? -eq 0 ]; then
            echo "✓ Downloaded $filename"
        else
            echo "✗ Failed to download $filename"
        fi
    fi
    echo ""
done

echo "========================================="
echo "Download Complete"
echo "========================================="
echo ""
echo "Files in $DATA_DIR:"
ls -lh "$DATA_DIR"/*.parquet 2>/dev/null || echo "No parquet files found"
