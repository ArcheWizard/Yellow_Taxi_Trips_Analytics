"""
Pydantic models for API request/response schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Base response model
class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Number of records per page")
    offset: int = Field(..., description="Number of records skipped")

    model_config = ConfigDict(from_attributes=True)


# Ride models
class RideBase(BaseModel):
    """Base ride model with common fields."""

    vendor_id: int = Field(..., description="Vendor ID (1 or 2)")
    pickup_datetime: datetime = Field(..., description="Pickup timestamp")
    dropoff_datetime: datetime = Field(..., description="Dropoff timestamp")
    passenger_count: Optional[int] = Field(None, description="Number of passengers")
    trip_distance: Decimal = Field(..., description="Trip distance in miles")
    pickup_location_id: Optional[int] = Field(None, description="Pickup zone ID")
    dropoff_location_id: Optional[int] = Field(None, description="Dropoff zone ID")
    rate_code_id: Optional[int] = Field(None, description="Rate code")
    store_and_fwd_flag: Optional[str] = Field(
        None, description="Store and forward flag"
    )
    payment_type: int = Field(..., description="Payment type (1-6)")
    fare_amount: Decimal = Field(..., description="Base fare amount")
    extra: Optional[Decimal] = Field(None, description="Extra charges")
    mta_tax: Optional[Decimal] = Field(None, description="MTA tax")
    tip_amount: Optional[Decimal] = Field(None, description="Tip amount")
    tolls_amount: Optional[Decimal] = Field(None, description="Tolls amount")
    improvement_surcharge: Optional[Decimal] = Field(
        None, description="Improvement surcharge"
    )
    total_amount: Decimal = Field(..., description="Total amount")
    congestion_surcharge: Optional[Decimal] = Field(
        None, description="Congestion surcharge"
    )
    airport_fee: Optional[Decimal] = Field(None, description="Airport fee")

    model_config = ConfigDict(from_attributes=True)


class Ride(RideBase):
    """Complete ride model with ID."""

    ride_id: int = Field(..., description="Unique ride identifier")
    created_at: Optional[datetime] = Field(
        None, description="Record creation timestamp"
    )

    model_config = ConfigDict(from_attributes=True)


class RideListResponse(BaseModel):
    """Response model for paginated list of rides."""

    data: List[Ride]
    metadata: PaginationMetadata

    model_config = ConfigDict(from_attributes=True)


# Analytics models
class HourlyStat(BaseModel):
    """Hourly statistics model."""

    date: datetime
    hour: int
    trip_count: int
    total_revenue: Decimal
    avg_distance: Decimal
    avg_fare: Decimal
    avg_duration_min: Decimal
    credit_card_count: int
    cash_count: int

    model_config = ConfigDict(from_attributes=True)


class LocationStat(BaseModel):
    """Location statistics model."""

    location_id: int
    borough: Optional[str]
    zone: Optional[str]
    trip_count: int
    avg_distance: Decimal
    avg_fare: Decimal
    avg_tip: Decimal
    pct_of_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class VendorDailyPerformance(BaseModel):
    """Vendor daily performance model."""

    vendor_id: int
    vendor_name: str
    date: datetime
    trip_count: int
    total_revenue: Decimal
    avg_fare: Decimal
    avg_trip_distance: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentHourlyStat(BaseModel):
    """Payment type hourly statistics."""

    hour: int
    payment_type: int
    trip_count: int
    total_amount: Decimal
    avg_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class DistanceSegment(BaseModel):
    """Distance segment statistics."""

    segment: str
    trip_count: int
    avg_fare: Decimal
    avg_tip: Decimal
    pct_of_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class TimePattern(BaseModel):
    """Time pattern statistics."""

    day_of_week: int
    hour: int
    trip_count: int
    avg_fare: Decimal
    avg_distance: Decimal

    model_config = ConfigDict(from_attributes=True)


class PopularRoute(BaseModel):
    """Popular route statistics."""

    pickup_location_id: int
    dropoff_location_id: int
    pickup_zone: Optional[str]
    dropoff_zone: Optional[str]
    trip_count: int
    avg_fare: Decimal
    avg_distance: Decimal
    avg_duration_min: Decimal

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummary(BaseModel):
    """Overall analytics summary."""

    total_trips: int
    total_revenue: Decimal
    avg_fare: Decimal
    avg_distance: Decimal
    avg_duration_min: Decimal
    date_range_start: Optional[datetime]
    date_range_end: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Health check models
class HealthCheck(BaseModel):
    """Health check response."""

    status: str = Field(..., description="API status")
    database: str = Field(..., description="Database status")
    timestamp: datetime = Field(..., description="Current timestamp")

    model_config = ConfigDict(from_attributes=True)


class WelcomeMessage(BaseModel):
    """Welcome message response."""

    message: str
    version: str
    status: str
    docs_url: str

    model_config = ConfigDict(from_attributes=True)
