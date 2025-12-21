"""
Rides endpoints for CRUD operations.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.models import PaginationMetadata, Ride, RideListResponse
from src.api.services.database import db_service

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()


@router.get("/rides", response_model=RideListResponse)
async def get_rides(
    limit: int = Query(
        default=100, ge=1, le=1000, description="Number of records to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    vendor_id: Optional[int] = Query(
        default=None, ge=1, le=2, description="Filter by vendor ID (1 or 2)"
    ),
    payment_type: Optional[int] = Query(
        default=None, ge=1, le=6, description="Filter by payment type (1-6)"
    ),
    date_from: Optional[datetime] = Query(
        default=None, description="Filter rides from this date"
    ),
    date_to: Optional[datetime] = Query(
        default=None, description="Filter rides until this date"
    ),
):
    """
    Get paginated list of rides.

    Query Parameters:
    - **limit**: Number of records to return (default: 100, max: 1000)
    - **offset**: Number of records to skip for pagination (default: 0)
    - **vendor_id**: Filter by vendor (1=Creative Mobile Tech, 2=VeriFone)
    - **payment_type**: Filter by payment type (1=Credit, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided)
    - **date_from**: Start date for filtering (ISO 8601 format)
    - **date_to**: End date for filtering (ISO 8601 format)

    Returns:
    - List of rides with pagination metadata
    """
    try:
        result = db_service.get_rides(
            limit=limit,
            offset=offset,
            vendor_id=vendor_id,
            payment_type=payment_type,
            date_from=date_from,
            date_to=date_to,
        )

        return RideListResponse(
            data=[Ride(**ride) for ride in result["data"]],
            metadata=PaginationMetadata(
                total=result["total"], limit=limit, offset=offset
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rides: {str(e)}")


@router.get("/rides/{ride_id}", response_model=Ride)
async def get_ride_by_id(ride_id: int):
    """
    Get a specific ride by ID.

    Path Parameters:
    - **ride_id**: Unique ride identifier

    Returns:
    - Ride details

    Raises:
    - 404: Ride not found
    """
    try:
        ride = db_service.get_ride_by_id(ride_id)

        if not ride:
            raise HTTPException(
                status_code=404, detail=f"Ride with ID {ride_id} not found"
            )

        return Ride(**ride)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ride: {str(e)}")
