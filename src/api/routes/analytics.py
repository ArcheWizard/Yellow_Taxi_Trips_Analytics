"""
Analytics endpoints for accessing pre-computed statistics.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from src.api.models import (
    AnalyticsSummary,
    DistanceSegment,
    HourlyStat,
    LocationStat,
    PaymentHourlyStat,
    PopularRoute,
    TimePattern,
    VendorDailyPerformance,
)
from src.api.services.database import db_service
from fastapi import APIRouter, HTTPException, Query

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    date_from: Optional[datetime] = Query(
        default=None, description="Start date for analysis"
    ),
    date_to: Optional[datetime] = Query(
        default=None, description="End date for analysis"
    ),
):
    """
    Get overall analytics summary.

    Query Parameters:
    - **date_from**: Start date for filtering (ISO 8601 format)
    - **date_to**: End date for filtering (ISO 8601 format)

    Returns:
    - Overall statistics including trip count, revenue, averages
    """
    try:
        result = db_service.get_analytics_summary(date_from=date_from, date_to=date_to)
        return AnalyticsSummary(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")


@router.get("/hourly", response_model=List[HourlyStat])
async def get_hourly_stats(
    limit: int = Query(
        default=100, ge=1, le=500, description="Number of records to return"
    ),
):
    """
    Get hourly trip statistics.

    Query Parameters:
    - **limit**: Number of records to return (default: 100, max: 500)

    Returns:
    - List of hourly statistics with trip counts, revenue, and payment types
    """
    try:
        results = db_service.get_hourly_stats(limit=limit)
        return [HourlyStat(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching hourly stats: {str(e)}"
        )


@router.get("/locations/pickup", response_model=List[LocationStat])
async def get_top_pickup_locations(
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of locations to return"
    ),
):
    """
    Get top pickup locations.

    Query Parameters:
    - **limit**: Number of locations to return (default: 20, max: 100)

    Returns:
    - List of top pickup locations with statistics
    """
    try:
        results = db_service.get_top_pickup_locations(limit=limit)
        return [LocationStat(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pickup locations: {str(e)}"
        )


@router.get("/locations/dropoff", response_model=List[LocationStat])
async def get_top_dropoff_locations(
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of locations to return"
    ),
):
    """
    Get top dropoff locations.

    Query Parameters:
    - **limit**: Number of locations to return (default: 20, max: 100)

    Returns:
    - List of top dropoff locations with statistics
    """
    try:
        results = db_service.get_top_dropoff_locations(limit=limit)
        # Rename 'dropoff_count' to 'trip_count' for the LocationStat model
        for stat in results:
            stat["trip_count"] = stat.pop("dropoff_count")
        return [LocationStat(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching dropoff locations: {str(e)}"
        )


@router.get("/vendors/performance", response_model=List[VendorDailyPerformance])
async def get_vendor_performance(
    limit: int = Query(
        default=30, ge=1, le=100, description="Number of records to return"
    ),
):
    """
    Get vendor daily performance statistics.

    Query Parameters:
    - **limit**: Number of records to return (default: 30, max: 100)

    Returns:
    - List of vendor performance metrics by date
    """
    try:
        results = db_service.get_vendor_performance(limit=limit)
        return [VendorDailyPerformance(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching vendor performance: {str(e)}"
        )


@router.get("/payment/hourly", response_model=List[PaymentHourlyStat])
async def get_payment_hourly_stats():
    """
    Get payment type distribution by hour.

    Returns:
    - List of payment statistics grouped by hour and payment type
    """
    try:
        results = db_service.get_payment_hourly_stats()
        return [PaymentHourlyStat(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching payment stats: {str(e)}"
        )


@router.get("/distance/segments", response_model=List[DistanceSegment])
async def get_distance_segments():
    """
    Get trip statistics by distance segments.

    Returns:
    - List of statistics for each distance segment (0-2, 2-5, 5-10, 10-20, 20+ miles)
    """
    try:
        results = db_service.get_distance_segments()
        return [DistanceSegment(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching distance segments: {str(e)}"
        )


@router.get("/patterns/time", response_model=List[TimePattern])
async def get_time_patterns(
    limit: int = Query(
        default=168, ge=1, le=500, description="Number of records to return"
    ),
):
    """
    Get time-based patterns (day of week + hour).

    Query Parameters:
    - **limit**: Number of records to return (default: 168 for full week, max: 500)

    Returns:
    - List of trip patterns by day of week and hour
    """
    try:
        results = db_service.get_time_patterns(limit=limit)
        return [TimePattern(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching time patterns: {str(e)}"
        )


@router.get("/routes/popular", response_model=List[PopularRoute])
async def get_popular_routes(
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of routes to return"
    ),
):
    """
    Get most popular routes (pickup-dropoff pairs).

    Query Parameters:
    - **limit**: Number of routes to return (default: 20, max: 100)

    Returns:
    - List of popular routes with trip counts and average metrics
    """
    try:
        results = db_service.get_popular_routes(limit=limit)
        return [PopularRoute(**stat) for stat in results]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching popular routes: {str(e)}"
        )
