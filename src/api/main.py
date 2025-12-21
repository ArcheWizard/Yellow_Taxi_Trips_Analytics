"""
City Rides Analytics API - FastAPI Application
Main application file with route configuration and middleware.
"""

import logging
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.routes import analytics, health, rides

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="City Rides Analytics API",
    description="REST API for NYC Yellow Taxi trip data and analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track response times for performance monitoring
response_times = defaultdict(list)


# Middleware to log response time
@app.middleware("http")
async def log_response_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000  # Convert to ms

    # Track response times by endpoint
    endpoint = f"{request.method} {request.url.path}"
    response_times[endpoint].append(duration)

    # Add response time header
    response.headers["X-Response-Time"] = f"{duration:.2f}ms"

    # Log with statistics
    times = response_times[endpoint]
    avg_time = statistics.mean(times) if times else duration

    logger.info(
        f"{endpoint} - {duration:.2f}ms (avg: {avg_time:.2f}ms, samples: {len(times)})"
    )

    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "message": str(exc)}
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(rides.router, prefix="/api/v1", tags=["Rides"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get API performance metrics.

    Returns:
        Dictionary with performance statistics for each endpoint
    """
    metrics = {}
    for endpoint, times in response_times.items():
        if times:
            sorted_times = sorted(times)
            count = len(times)
            metrics[endpoint] = {
                "count": count,
                "min_ms": round(min(times), 2),
                "max_ms": round(max(times), 2),
                "avg_ms": round(statistics.mean(times), 2),
                "median_ms": round(statistics.median(times), 2),
                "p95_ms": round(
                    sorted_times[int(count * 0.95)] if count >= 20 else max(times), 2
                ),
                "p99_ms": round(
                    sorted_times[int(count * 0.99)] if count >= 100 else max(times), 2
                ),
            }
    return {
        "endpoints": metrics,
        "total_requests": sum(len(times) for times in response_times.values()),
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("City Rides Analytics API starting up...")
    logger.info("Documentation available at: http://localhost:8000/docs")
    logger.info("Connection pooling enabled: 2-20 connections")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information and close database connections."""
    logger.info("City Rides Analytics API shutting down...")

    # Close all database connections
    try:
        from config.database import DatabaseConfig

        db_config = DatabaseConfig()
        db_config.close_all_connections()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
