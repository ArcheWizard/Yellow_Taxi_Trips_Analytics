"""
Health check endpoints for API status monitoring.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.models import HealthCheck, WelcomeMessage
from src.api.services.database import db_service

router = APIRouter()


@router.get("/", response_model=WelcomeMessage)
async def root():
    """
    Welcome endpoint - API information.

    Returns basic information about the API.
    """
    return WelcomeMessage(
        message="City Rides Analytics API",
        version="1.0.0",
        status="running",
        docs_url="/docs"
    )


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint.

    Checks API and database connectivity status.
    Returns 200 if healthy, 503 if database is unavailable.
    """
    db_status = "healthy" if db_service.test_connection() else "unhealthy"

    if db_status == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

    return HealthCheck(
        status="healthy",
        database=db_status,
        timestamp=datetime.now()
    )
