# API Documentation

## 🚀 FastAPI Application

## Overview

The City Rides Analytics API provides RESTful endpoints for accessing NYC taxi trip data and analytics. Built with FastAPI, it offers automatic API documentation, data validation, and high performance.

## Base URL

```text
http://localhost:8000
```

## Authentication

*Currently, the API is unauthenticated. Authentication will be added in Phase 3.*

## API Endpoints

### Health Check

#### GET `/`

Welcome endpoint to verify API is running.

**Response:**

```json
{
  "message": "City Rides Analytics API",
  "version": "0.1.0",
  "status": "running"
}
```

#### GET `/health`

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-11-02T10:30:00Z"
}
```

### Rides Endpoints

#### GET `/api/v1/rides`

Get paginated list of rides.

**Query Parameters:**

- `limit` (int, optional): Number of records to return (default: 100, max: 1000)
- `offset` (int, optional): Number of records to skip (default: 0)
- `vendor_id` (int, optional): Filter by vendor ID
- `payment_type` (int, optional): Filter by payment type
- `date_from` (datetime, optional): Filter rides from this date
- `date_to` (datetime, optional): Filter rides until this date

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/rides?limit=10&vendor_id=1"
```

**Example Response:**

```json
{
  "total": 100000,
  "limit": 10,
  "offset": 0,
  "data": [
    {
      "ride_id": 1,
      "vendor_id": 1,
      "pickup_datetime": "2024-11-01T08:30:00",
      "dropoff_datetime": "2024-11-01T08:45:00",
      "passenger_count": 1,
      "trip_distance": 2.5,
      "pickup_location_id": 161,
      "dropoff_location_id": 234,
      "payment_type": 1,
      "fare_amount": 12.50,
      "total_amount": 15.80
    }
  ]
}
```

#### GET `/api/v1/rides/{ride_id}`

Get a specific ride by ID.

**Path Parameters:**

- `ride_id` (int): The ride ID

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/rides/12345"
```

**Example Response:**

```json
{
  "ride_id": 12345,
  "vendor_id": 2,
  "pickup_datetime": "2024-11-01T14:20:00",
  "dropoff_datetime": "2024-11-01T14:35:00",
  "passenger_count": 2,
  "trip_distance": 3.2,
  "pickup_location_id": 132,
  "dropoff_location_id": 170,
  "rate_code_id": 1,
  "store_and_fwd_flag": "N",
  "payment_type": 1,
  "fare_amount": 14.00,
  "extra": 0.50,
  "mta_tax": 0.50,
  "tip_amount": 2.80,
  "tolls_amount": 0.00,
  "improvement_surcharge": 0.30,
  "total_amount": 18.10,
  "congestion_surcharge": 2.50,
  "airport_fee": 0.00
}
```

### Analytics Endpoints

#### GET `/api/v1/analytics/summary`

Get overall summary statistics.

**Query Parameters:**

- `date_from` (datetime, optional): Start date for analysis
- `date_to` (datetime, optional): End date for analysis

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/analytics/summary?date_from=2024-11-01&date_to=2024-11-30"
```

**Example Response:**

```json
{
  "total_trips": 100000,
  "total_revenue": 1850000.50,
  "avg_fare": 18.50,
  "avg_distance": 3.2,
  "avg_duration_minutes": 15.5,
  "total_tips": 185000.25,
  "period": {
    "from": "2024-11-01T00:00:00",
    "to": "2024-11-30T23:59:59"
  }
}
```

#### GET `/api/v1/analytics/hourly`

Get hourly trip statistics.

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/analytics/hourly"
```

**Example Response:**

```json
{
  "data": [
    {
      "hour": 0,
      "trip_count": 1500,
      "avg_fare": 16.50,
      "total_revenue": 24750.00
    },
    {
      "hour": 1,
      "trip_count": 1200,
      "avg_fare": 17.20,
      "total_revenue": 20640.00
    }
  ]
}
```

#### GET `/api/v1/analytics/daily`

Get daily trip statistics.

**Query Parameters:**

- `days` (int, optional): Number of days to include (default: 30)

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/analytics/daily?days=7"
```

**Example Response:**

```json
{
  "data": [
    {
      "date": "2024-11-01",
      "trip_count": 3500,
      "revenue": 65000.00,
      "avg_fare": 18.57,
      "avg_distance": 3.1
    }
  ]
}
```

#### GET `/api/v1/analytics/top-locations`

Get top pickup and dropoff locations.

**Query Parameters:**

- `limit` (int, optional): Number of locations to return (default: 20)
- `type` (str, optional): "pickup" or "dropoff" (default: "pickup")

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/analytics/top-locations?limit=10&type=pickup"
```

**Example Response:**

```json
{
  "type": "pickup",
  "data": [
    {
      "location_id": 161,
      "zone_name": "Midtown Center",
      "borough": "Manhattan",
      "trip_count": 5432,
      "avg_fare": 19.80
    }
  ]
}
```

#### GET `/api/v1/analytics/revenue-by-payment`

Get revenue breakdown by payment type.

**Example Response:**

```json
{
  "data": [
    {
      "payment_type": 1,
      "payment_method": "Credit Card",
      "trip_count": 75000,
      "total_revenue": 1425000.00,
      "avg_fare": 19.00,
      "avg_tip": 3.20
    },
    {
      "payment_type": 2,
      "payment_method": "Cash",
      "trip_count": 25000,
      "total_revenue": 425000.50,
      "avg_fare": 17.00,
      "avg_tip": 0.00
    }
  ]
}
```

### Vendor Endpoints

#### GET `/api/v1/vendors`

Get list of all vendors.

**Example Response:**

```json
{
  "data": [
    {
      "vendor_id": 1,
      "vendor_name": "Creative Mobile Technologies"
    },
    {
      "vendor_id": 2,
      "vendor_name": "VeriFone Inc."
    }
  ]
}
```

#### GET `/api/v1/vendors/{vendor_id}/metrics`

Get performance metrics for a specific vendor.

**Query Parameters:**

- `date_from` (datetime, optional): Start date
- `date_to` (datetime, optional): End date

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/vendors/1/metrics"
```

**Example Response:**

```json
{
  "vendor_id": 1,
  "vendor_name": "Creative Mobile Technologies",
  "metrics": {
    "total_trips": 55000,
    "total_revenue": 1050000.00,
    "avg_fare": 19.09,
    "avg_distance": 3.3,
    "market_share": 55.0
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid parameter: limit must be between 1 and 1000"
}
```

### 404 Not Found

```json
{
  "detail": "Ride with ID 99999 not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["query", "date_from"],
      "msg": "invalid datetime format",
      "type": "value_error"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "error": "Database connection failed"
}
```

## Running the API

### Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main:app --bind 0.0.0.0:8000
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get rides
curl "http://localhost:8000/api/v1/rides?limit=5"

# Get analytics summary
curl http://localhost:8000/api/v1/analytics/summary

# Get specific ride
curl http://localhost:8000/api/v1/rides/1
```

### Using Python requests

```python
import requests

base_url = "http://localhost:8000"

# Get summary
response = requests.get(f"{base_url}/api/v1/analytics/summary")
data = response.json()
print(data)

# Get rides with filters
params = {
    "limit": 10,
    "vendor_id": 1,
    "date_from": "2024-11-01"
}
response = requests.get(f"{base_url}/api/v1/rides", params=params)
rides = response.json()
print(rides)
```

### Using httpie

```bash
# Install httpie
pip install httpie

# Make requests
http GET http://localhost:8000/api/v1/analytics/summary
http GET http://localhost:8000/api/v1/rides limit==10 vendor_id==1
```

## Rate Limiting

*Rate limiting will be implemented in Phase 3.*

Planned limits:

- 100 requests per minute per IP
- 1000 requests per hour per IP

## Caching

*Caching will be implemented in Phase 5.*

Planned caching strategy:

- Redis for frequently accessed analytics
- TTL: 5 minutes for real-time metrics, 1 hour for historical data

## Webhooks

*Webhooks not yet implemented.*

---

**Last Updated:** November 2, 2025
**API Version:** 0.1.0
