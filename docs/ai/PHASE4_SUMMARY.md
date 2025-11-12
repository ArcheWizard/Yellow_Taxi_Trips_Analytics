# Phase 4: Metabase Dashboard Development

**Status:** 🚧 IN PROGRESS - Setup complete, dashboards pending
**Date:** November 8-9, 2025

## ✅ Prerequisites Complete

- ✅ Metabase running on <http://localhost:3000>
- ✅ PostgreSQL connection successful
- ✅ Database synced (3 tables + 8 materialized views)
- ✅ 93,171 rides loaded
- ✅ All data validated

## 🚧 Pending Tasks

- [ ] Complete initial Metabase setup wizard
- [ ] Create Overview Dashboard
- [ ] Create Time Analysis Dashboard
- [ ] Create Location Dashboard
- [ ] Create Financial Dashboard

---

## 📊 Dashboard 1: Overview Dashboard

### Overview Goal

High-level KPIs and trends for quick insights

#### 1. **KPI Cards (Top Row)**

#### 1. Total Trips

```sql
SELECT COUNT(*) as total_trips FROM rides;
```

#### 2. Total Revenue

```sql
SELECT ROUND(SUM(total_amount)::numeric, 2) as total_revenue
FROM rides
WHERE total_amount > 0;
```

#### 3. Average Fare

```sql
SELECT ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
WHERE total_amount > 0;
```

#### Average Distance

```sql
SELECT ROUND(AVG(trip_distance)::numeric, 2) as avg_distance
FROM rides
WHERE trip_distance > 0;
```

#### 2. **Daily Trend Chart**

```sql
SELECT
    DATE(pickup_datetime) as date,
    COUNT(*) as trips,
    ROUND(SUM(total_amount)::numeric, 2) as revenue
FROM rides
GROUP BY DATE(pickup_datetime)
ORDER BY date;
```

**Chart Type:** Line chart with dual Y-axis (trips and revenue)

#### 3. **Top 5 Pickup Locations**

```sql
SELECT
    zone,
    borough,
    pickup_count as trips
FROM mv_top_pickup_locations
ORDER BY pickup_count DESC
LIMIT 5;
```

**Chart Type:** Bar chart

#### 4. **Revenue by Payment Type**

```sql
SELECT
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        ELSE 'Other'
    END as payment_method,
    ROUND(SUM(total_amount)::numeric, 2) as revenue
FROM rides
GROUP BY payment_type
ORDER BY revenue DESC;
```

**Chart Type:** Pie chart

### Dashboard Layout

```text
┌────────────┬────────────┬────────────┬────────────┐
│ Total Trips│Total Revenue│  Avg Fare  │ Avg Dist   │
│   93,171   │  $3.08M    │   $33.13   │  4.59 mi   │
├────────────┴────────────┴────────────┴────────────┤
│                                                    │
│         Daily Trips & Revenue Trend                │
│              (Line Chart)                          │
│                                                    │
├──────────────────────┬─────────────────────────────┤
│                      │                             │
│  Top 5 Pickup        │   Revenue by Payment        │
│  Locations           │   Type (Pie Chart)          │
│  (Bar Chart)         │                             │
│                      │                             │
└──────────────────────┴─────────────────────────────┘
```

---

## 📊 Dashboard 2: Time Analysis Dashboard

### Time Analysis Goal

Understand temporal patterns and peak hours

### Metrics to Display

#### 1. **Hourly Heatmap**

```sql
SELECT
    day_of_week,
    day_name,
    hour,
    trip_count
FROM mv_time_patterns
ORDER BY day_of_week, hour;
```

**Chart Type:** Heatmap with days on Y-axis, hours on X-axis

#### 2. **Peak Hours Indicator**

```sql
SELECT
    hour,
    SUM(trip_count) as total_trips,
    ROUND(AVG(avg_fare)::numeric, 2) as avg_fare
FROM mv_time_patterns
GROUP BY hour
ORDER BY total_trips DESC
LIMIT 5;
```

**Chart Type:** Bar chart

#### 3. **Weekday vs Weekend**

```sql
SELECT
    CASE
        WHEN day_of_week IN (0, 6) THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    COUNT(*) as trips,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare
FROM rides
GROUP BY day_type;
```

**Chart Type:** Comparison cards

#### 4. **Hourly Revenue Trends**

```sql
SELECT
    hour,
    ROUND(SUM(total_revenue)::numeric, 2) as revenue
FROM mv_hourly_stats
GROUP BY hour
ORDER BY hour;
```

**Chart Type:** Area chart

### Dashboard Layout

```text
┌───────────────────────────────────────────────────┐
│                                                   │
│          Hourly Heatmap (Day x Hour)              │
│                                                   │
├──────────────────────┬────────────────────────────┤
│  Peak Hours Top 5    │  Weekday vs Weekend        │
│  (Bar Chart)         │  (Comparison Cards)        │
├──────────────────────┴────────────────────────────┤
│                                                   │
│          Hourly Revenue Trends (Area)             │
│                                                   │
└───────────────────────────────────────────────────┘
```

---

## 📊 Dashboard 3: Location Dashboard

### Location Goal

Geographic insights and route analysis

### Metrics to Display

#### 1. **Top Pickup Zones**

```sql
SELECT
    zone,
    borough,
    pickup_count,
    ROUND(avg_fare::numeric, 2) as avg_fare
FROM mv_top_pickup_locations
ORDER BY pickup_count DESC
LIMIT 10;
```

**Chart Type:** Table with conditional formatting

#### 2. **Top Dropoff Zones**

```sql
SELECT
    zone,
    borough,
    dropoff_count,
    ROUND(avg_fare::numeric, 2) as avg_fare
FROM mv_top_dropoff_locations
ORDER BY dropoff_count DESC
LIMIT 10;
```

**Chart Type:** Table

#### 3. **Borough Comparison**

```sql
SELECT
    borough,
    COUNT(*) as trips,
    ROUND(AVG(total_amount)::numeric, 2) as avg_fare,
    ROUND(SUM(total_amount)::numeric, 2) as total_revenue
FROM rides r
JOIN zones z ON r.pickup_location_id = z.location_id
WHERE z.borough IS NOT NULL
GROUP BY borough
ORDER BY trips DESC;
```

**Chart Type:** Bar chart

#### 4. **Popular Routes**

```sql
SELECT
    pickup_zone || ' → ' || dropoff_zone as route,
    trip_count,
    ROUND(avg_fare::numeric, 2) as avg_fare
FROM mv_popular_routes
ORDER BY trip_count DESC
LIMIT 10;
```

**Chart Type:** Table

### Dashboard Layout

```text
┌──────────────────────┬────────────────────────────┐
│                      │                            │
│  Top Pickup Zones    │  Top Dropoff Zones         │
│  (Table)             │  (Table)                   │
│                      │                            │
├──────────────────────┴────────────────────────────┤
│                                                   │
│          Borough Comparison (Bar Chart)           │
│                                                   │
├───────────────────────────────────────────────────┤
│                                                   │
│          Popular Routes (Table)                   │
│                                                   │
└───────────────────────────────────────────────────┘
```

---

## 📊 Dashboard 4: Financial Dashboard

### Financial Goal

Revenue analysis and financial metrics

### Metrics to Display

#### 1. **Revenue Breakdown**

```sql
SELECT
    ROUND(SUM(fare_amount)::numeric, 2) as base_fare,
    ROUND(SUM(tip_amount)::numeric, 2) as tips,
    ROUND(SUM(extra)::numeric, 2) as extras,
    ROUND(SUM(tolls_amount)::numeric, 2) as tolls,
    ROUND(SUM(congestion_surcharge)::numeric, 2) as congestion
FROM rides;
```

**Chart Type:** Stacked bar chart

#### 2. **Payment Distribution**

```sql
SELECT
    hour,
    payment_method,
    trip_count,
    ROUND(total_amount::numeric, 2) as revenue
FROM mv_payment_hourly
ORDER BY hour;
```

**Chart Type:** Stacked area chart

#### 3. **Distance-Based Pricing**

```sql
SELECT
    segment,
    trip_count,
    ROUND(avg_fare::numeric, 2) as avg_fare
FROM mv_distance_segments
ORDER BY CASE segment
    WHEN '0-1 miles' THEN 1
    WHEN '1-2 miles' THEN 2
    WHEN '2-5 miles' THEN 3
    WHEN '5-10 miles' THEN 4
    WHEN '10-20 miles' THEN 5
    WHEN '20+ miles' THEN 6
END;
```

**Chart Type:** Line chart

#### 4. **Tip Analysis (Credit Card Only)**

```sql
SELECT
    ROUND((tip_amount / NULLIF(fare_amount, 0) * 100)::numeric, 2) as tip_percentage,
    COUNT(*) as trips
FROM rides
WHERE payment_type = 1 AND tip_amount > 0
GROUP BY ROUND((tip_amount / NULLIF(fare_amount, 0) * 100)::numeric, 2)
ORDER BY tip_percentage;
```

**Chart Type:** Histogram

---

## 🎨 Metabase Step-by-Step Instructions

### Step 1: Create First Dashboard (Overview)

1. **Login to Metabase**: <http://localhost:3000>
2. Click **"New"** → **"Dashboard"**
3. Name: "🏠 Overview Dashboard"
4. Description: "High-level KPIs and trends"
5. Click **"Create"**

### Step 2: Add KPI Cards

1. Click **"Add a question"**
2. Select **"Custom question"**
3. Choose database: **"City Rides Analytics"**
4. Click **"Native query"** (to write SQL)
5. Paste the SQL query for Total Trips
6. Click **"Visualize"**
7. Change visualization to **"Number"**
8. Click **"Save"** → Add to "Overview Dashboard"
9. Repeat for other KPIs

### Step 3: Add Charts

For each chart:

1. Click **"Add a question"**
2. Write/paste SQL query
3. Choose appropriate visualization type
4. Configure axes and colors
5. Save to dashboard

### Step 4: Arrange Dashboard

1. Click **"Edit dashboard"**
2. Drag and resize cards
3. Add text cards for sections
4. Set auto-refresh (optional)
5. Click **"Save"**

### Step 5: Add Filters (Interactive)

1. Click **"Edit dashboard"**
2. Click **"Add a filter"**
3. Choose **"Date Range"**
4. Connect to date fields in questions
5. Add more filters (Vendor, Borough, etc.)
6. Save

---

## 🔄 Materialized View Refresh

Before building dashboards, ensure data is fresh:

```bash
cd ~/Coding/Big\ Data/MyProjects/Yellow_Taxi_Trips_Analytics
./scripts/refresh_materialized_views.sh
```

---

## ✅ Dashboard Checklist

### Overview Dashboard

- [ ] Total trips KPI
- [ ] Total revenue KPI
- [ ] Average fare KPI
- [ ] Average distance KPI
- [ ] Daily trend chart
- [ ] Top pickup locations
- [ ] Payment distribution

### Time Analysis Dashboard

- [ ] Hourly heatmap
- [ ] Peak hours chart
- [ ] Weekday vs weekend comparison
- [ ] Hourly revenue trends

### Location Dashboard

- [ ] Top pickup zones table
- [ ] Top dropoff zones table
- [ ] Borough comparison chart
- [ ] Popular routes table

### Financial Dashboard

- [ ] Revenue breakdown
- [ ] Payment distribution over time
- [ ] Distance-based pricing
- [ ] Tip analysis histogram

---

## 🎯 Next Steps

Once dashboards are built:

1. **Share dashboards** with stakeholders
2. **Set up email subscriptions** for daily reports
3. **Create public links** (if needed)
4. **Export as PDFs** for presentations
5. **Monitor performance** and optimize queries

---

**Need Help?**

- Metabase Docs: <https://www.metabase.com/docs/latest/>
- SQL queries are in: `sql/queries/`
- Materialized views: `sql/materialized_views.sql`

**Status:** Ready to build! 🚀
