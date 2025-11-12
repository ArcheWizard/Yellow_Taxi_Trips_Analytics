# Metabase Setup Guide

## 🎯 Metabase Dashboard Platform

**Status:** ✅ Container Running - Ready for dashboard creation
**Last Updated:** November 9, 2025

Metabase is installed and ready for dashboard creation!

## 🌐 Access Information

**URL:** <http://localhost:3000>

**Container:** `metabase` (Docker)

## 📝 Initial Setup Steps

### 1. First-Time Setup (Required)

Visit <http://localhost:3000> and complete the setup wizard:

1. **Language Selection:** Choose your preferred language
2. **Create Admin Account:**
   - Email: <your_email@example.com>
   - Password: (choose a secure password)
   - First Name: Your Name
   - Last Name: Your Last Name

3. **Skip** the "Add your data" step for now (we'll do it manually)

### 2. Add PostgreSQL Database Connection

After completing initial setup:

1. Click **Settings** (gear icon) → **Admin Settings** → **Databases** → **Add database**

2. **Connection Details:**

   ```text
   Database type: PostgreSQL
   Name: City Rides Analytics
   Host: host.docker.internal
   Port: 5432
   Database name: city_rides_db
   Username: rides_user
   Password: your_secure_password
   ```

3. Click **Save** and wait for schema sync

### 3. Verify Connection

After successful connection, you should see:

- ✅ **Tables (3):** vendors, zones, rides
- ✅ **Materialized Views (8):**
  - mv_hourly_stats
  - mv_top_pickup_locations
  - mv_top_dropoff_locations
  - mv_vendor_daily_performance
  - mv_payment_hourly
  - mv_distance_segments
  - mv_time_patterns
  - mv_popular_routes

## 📊 Dashboard Creation Plan

### Phase 4 Dashboards

1. **Overview Dashboard**
   - Total trips (KPI)
   - Total revenue (KPI)
   - Average fare (KPI)
   - Daily trend line
   - Top locations table

2. **Time Analysis Dashboard**
   - Hourly heatmap
   - Day-of-week patterns
   - Peak hours indicator
   - Weekly trends

3. **Location Dashboard**
   - Top pickup zones
   - Top dropoff zones
   - Popular routes
   - Borough comparison

4. **Financial Dashboard**
   - Revenue trends
   - Payment type distribution
   - Tip analysis
   - Fare distribution

## 🔄 Container Management

### Start Metabase

```bash
docker start metabase
```

### Stop Metabase

```bash
docker stop metabase
```

### View Logs

```bash
docker logs metabase -f
```

### Remove Container (if needed)

```bash
docker stop metabase
docker rm metabase
```

### Restart from Scratch

```bash
docker stop metabase
docker rm metabase
```bash
docker run -d -p 3000:3000 --name metabase \
  --add-host=host.docker.internal:host-gateway metabase/metabase
```

## 💾 Data Persistence

Metabase stores its configuration in an embedded H2 database inside the container. To persist data across container restarts, you can mount a volume:

```bash
docker run -d -p 3000:3000 \
  --name metabase \
  --add-host=host.docker.internal:host-gateway \
  -v metabase-data:/metabase-data \
  -e MB_DB_FILE=/metabase-data/metabase.db \
  metabase/metabase
```

## 🔒 Security Notes

- Change default passwords in production
- Use environment variables for sensitive data
- Configure HTTPS for production deployment
- Restrict access with authentication

## 📚 Resources

- **Metabase Documentation:** <https://www.metabase.com/docs/latest/>
- **Question Building:** <https://www.metabase.com/docs/latest/questions/start>
- **Dashboard Guide:** <https://www.metabase.com/docs/latest/dashboards/start>

## ✅ Next Steps

1. Complete initial setup at <http://localhost:3000>
2. Add database connection (see connection details above)
3. Create first question using materialized views
4. Build Overview Dashboard
5. Add interactive filters
