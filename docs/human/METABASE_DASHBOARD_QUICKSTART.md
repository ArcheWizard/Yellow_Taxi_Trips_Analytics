# Metabase Dashboard Quick Start Guide

**Goal:** Create 4 dashboards for NYC Taxi Analytics
**Time Required:** 20-30 minutes
**Access:** <http://localhost:3000>

---

## ✅ Pre-Setup Checklist

- ✅ Metabase running on <http://localhost:3000>
- ✅ PostgreSQL database connected
- ✅ 9 materialized views created and refreshed
- ✅ 93,171 rides loaded

---

## 🚀 Dashboard 1: Overview Dashboard (10 minutes)

### Step-by-Step Instructions

1. **Open Metabase** → <http://localhost:3000>
2. **Click "New"** → "Dashboard"
3. **Name it:** "Overview Dashboard"
4. **Click "Save"**

### Add Visualizations

#### KPI Card 1: Total Trips

1. Click **"Add a Question"**
2. Select **"Native Query (SQL)"**
3. Paste:

```sql
SELECT COUNT(*) as total_trips FROM rides;
```

4. **Run** → Choose **"Number"** visualization
2. **Settings** → Set number format with comma separators
3. **Save** → Add to "Overview Dashboard"

#### KPI Card 2: Total Revenue

1. **New Question** → **SQL**
2. Paste:

```sql
SELECT ROUND(SUM(total_amount)::numeric, 2) as total_revenue
FROM rides WHERE total_amount > 0;
```

3. **Number** visualization → Format as **Currency ($)**
2. **Save** to dashboard

#### KPI Card 3: Average Fare

1. **New Question** → **SQL**

```sql
SELECT ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides WHERE total_amount > 0;
```

2. **Number** viz → **Currency ($)** format
2. **Save** to dashboard

#### KPI Card 4: Average Distance

1. **New Question** → **SQL**

```sql
SELECT ROUND(AVG(trip_distance)::numeric, 2) as avg_distance
FROM rides WHERE trip_distance > 0;
```

2. **Number** viz → Add " miles" suffix
2. **Save** to dashboard

#### Chart 1: Daily Trips & Revenue

1. **New Question** → **SQL**

```sql
SELECT
    DATE(pickup_datetime) as date,
    COUNT(*) as trips,
    ROUND(SUM(total_amount)::numeric, 2) as revenue
FROM rides
GROUP BY DATE(pickup_datetime)
ORDER BY date;
```

2. Choose **"Line"** chart
2. X-axis: **date**, Y-axis: **trips** (left), **revenue** (right)
3. **Save** to dashboard

#### Chart 2: Top 5 Pickup Locations

1. **New Question** → **SQL**

```sql
SELECT zone, pickup_count as trips
FROM mv_top_pickup_locations
ORDER BY pickup_count DESC
LIMIT 5;
```

2. Choose **"Bar"** chart (horizontal)
2. X-axis: **zone**, Y-axis: **trips**
3. **Save** to dashboard

#### Chart 3: Revenue by Payment Type

1. **New Question** → **SQL**

```sql
SELECT
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Other'
    END as payment_method,
    ROUND(SUM(total_amount)::numeric, 2) as revenue
FROM rides
GROUP BY payment_type
ORDER BY revenue DESC;
```

2. Choose **"Pie"** chart
2. **Save** to dashboard

### Layout Tips

- Arrange KPI cards in a row at the top
- Place line chart below KPIs (full width)
- Put bar and pie charts side-by-side at bottom

---

## 📊 Dashboard 2: Time Analysis (8 minutes)

### Create Dashboard

1. **New Dashboard** → "Time Analysis"

### Add Visualizations

#### Heatmap: Hourly Patterns

1. **New SQL Question**:

```sql
SELECT
    TO_CHAR(pickup_datetime, 'Day') as day_name,
    EXTRACT(HOUR FROM pickup_datetime) as hour,
    COUNT(*) as trip_count
FROM rides
GROUP BY day_name, hour
ORDER BY
    CASE
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Sunday%' THEN 0
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Monday%' THEN 1
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Tuesday%' THEN 2
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Wednesday%' THEN 3
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Thursday%' THEN 4
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Friday%' THEN 5
        WHEN TO_CHAR(pickup_datetime, 'Day') LIKE 'Saturday%' THEN 6
    END, hour;
```

2. Choose **"Heat Map"** or **"Bar"** chart
2. **Save** to dashboard

#### Peak Hours

1. **New SQL Question**:

```sql
SELECT hour, SUM(trip_count) as total_trips
FROM mv_time_patterns
GROUP BY hour
ORDER BY total_trips DESC
LIMIT 5;
```

2. **Bar** chart
2. **Save**

#### Weekday vs Weekend

1. **New SQL Question**:

```sql
SELECT
    CASE
        WHEN EXTRACT(DOW FROM pickup_datetime) IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    COUNT(*) as trips,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
GROUP BY day_type;
```

2. **Table** or **Number** visualization
2. **Save**

#### Hourly Revenue

1. **New SQL Question**:

```sql
SELECT hour, ROUND(SUM(total_revenue)::numeric, 2) as revenue
FROM mv_hourly_stats
GROUP BY hour
ORDER BY hour;
```

2. **Area** chart
2. **Save**

---

## 🗺️ Dashboard 3: Location Analysis (5 minutes)

### Create Dashboard

1. **New Dashboard** → "Location Analysis"

### Add Visualizations

#### Top Pickup Zones

```sql
SELECT zone, borough, pickup_count, avg_fare
FROM mv_top_pickup_locations
ORDER BY pickup_count DESC
LIMIT 10;
```

- **Table** visualization

#### Top Dropoff Zones

```sql
SELECT zone, borough, dropoff_count, avg_fare
FROM mv_top_dropoff_locations
ORDER BY dropoff_count DESC
LIMIT 10;
```

- **Table** visualization

#### Popular Routes

```sql
SELECT
    pickup_zone || ' → ' || dropoff_zone as route,
    trip_count,
    avg_fare
FROM mv_popular_routes
ORDER BY trip_count DESC
LIMIT 15;
```

- **Table** visualization

---

## 📈 Dashboard 4: Performance Metrics (5 minutes)

### Create Dashboard

1. **New Dashboard** → "Performance Metrics"

### Add Visualizations

#### Vendor Performance

```sql
SELECT
    date,
    vendor_name,
    trip_count,
    total_revenue,
    avg_fare
FROM mv_vendor_daily_performance
ORDER BY date DESC
LIMIT 30;
```

- **Line** chart (date on X-axis, color by vendor)

#### Distance Segments

```sql
SELECT distance_segment, trip_count, avg_fare, median_fare
FROM mv_distance_segments
ORDER BY
    CASE distance_segment
        WHEN '0-1 miles' THEN 1
        WHEN '1-2 miles' THEN 2
        WHEN '2-5 miles' THEN 3
        WHEN '5-10 miles' THEN 4
        WHEN '10-20 miles' THEN 5
        WHEN '20+ miles' THEN 6
    END;
```

- **Bar** chart

#### Payment Method Distribution

```sql
SELECT payment_method, SUM(trip_count) as total_trips
FROM mv_payment_hourly
GROUP BY payment_method
ORDER BY total_trips DESC;
```

- **Pie** chart

---

## 🎨 Dashboard Styling Tips

### Colors

- Use **consistent color schemes** across dashboards
- Revenue → Green
- Trips/Count → Blue
- Distance → Orange

### Layout

- **Top row:** KPI cards (4 columns)
- **Middle:** Main charts (full width or 2 columns)
- **Bottom:** Supporting charts (2-3 columns)

### Filters

Add dashboard filters for:

- **Date Range** (pickup_datetime)
- **Vendor** (vendor_id)
- **Borough** (via zones table)

---

## ✅ Verification Checklist

After creating all dashboards, verify:

- [ ] All 4 dashboards created
- [ ] All SQL queries return data
- [ ] Charts display correctly
- [ ] KPI cards show numbers
- [ ] No error messages
- [ ] Dashboards load quickly (<2 seconds)

---

## 🔍 Troubleshooting

### Issue: Query returns no data

- Check materialized views are refreshed: `SELECT * FROM mv_analytics_summary;`
- Verify rides table has data: `SELECT COUNT(*) FROM rides;`

### Issue: Slow queries

- Ensure materialized views are being used (check query plans)
- Run benchmark again: `python src/analytics/benchmark_materialized_views.py`

### Issue: Chart doesn't display

- Try different visualization types
- Check column names match query output
- Verify data types are correct

---

## 📚 Reference

- Full SQL queries: `docs/ai/PHASE4_SUMMARY.md`
- API documentation: `docs/human/API.md`
- Database schema: `docs/ai/SCHEMA_REFERENCE.md`

---

## 🎯 Next Steps

After creating dashboards:

1. **Share** dashboards with team
2. **Set up refresh schedule** in Metabase settings
3. **Export** dashboards for reports
4. **Continue to Phase 5.2** - Incremental refresh optimization

---

**Estimated Total Time:** 30 minutes
**Questions?** Check `docs/human/METABASE_SETUP.md` for detailed Metabase configuration
