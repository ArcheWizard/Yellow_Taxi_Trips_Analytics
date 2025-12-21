# City Rides Analytics Dashboard

## 🎯 Project Overview

A comprehensive data analytics platform for analyzing NYC Yellow Taxi trip data using PostgreSQL, Python, and modern data engineering practices.

**Project Goals:**

- Analyze ride patterns and trends
- Evaluate driver/vendor performance metrics
- Understand customer behavior and preferences
- Build interactive analytics dashboard
- Create RESTful API for data access

## 📊 Data Source

### NYC Taxi & Limousine Commission (TLC) Dataset

- Dataset: Yellow Taxi Trip Records
- Source: <https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>
- Current Data: July-November 2025 (17.4M rows)
- File Format: Parquet
- Production Scale: 17,417,027 trips loaded

**Download Link:**

```text
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-11.parquet
```

## 🏗️ Architecture

```text
┌─────────────────┐
│   Data Source   │
│  (Parquet File) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ETL Pipeline   │
│    (Python)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│    Database     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────┐  ┌──────┐
│ API  │  │  BI  │
│FastAPI│ │Tools │
└──────┘  └──────┘
```

## 📁 Project Structure

```text
Yellow_Taxi_Trips_Analytics/
├── data/                          # Data files (gitignored)
│   └── yellow_tripdata_2024-11.parquet
├── docs/                          # Documentation
│   ├── human/                     # Human-readable docs
│   │   ├── README.md             # This file
│   │   ├── SETUP.md              # Setup instructions
│   │   ├── DATABASE.md           # Database schema & queries
│   │   ├── API.md                # API documentation
│   │   └── ANALYTICS.md          # Analytics & insights guide
│   └── ai/                        # AI assistant context
│       ├── PROJECT_CONTEXT.md    # Project structure & decisions
│       ├── DEVELOPMENT_GUIDE.md  # Development guidelines
│       └── SCHEMA_REFERENCE.md   # Database schema reference
├── sql/                           # SQL scripts
│   ├── schema.sql                # Database schema
│   ├── indexes.sql               # Index optimization
│   ├── views.sql                 # Materialized views
│   └── queries/                  # Analysis queries
│       ├── basic_analytics.sql
│       ├── advanced_analytics.sql
│       └── performance_metrics.sql
├── src/                           # Source code
│   ├── etl/                      # ETL pipeline
│   │   ├── __init__.py
│   │   ├── load_data.py         # Main ETL script
│   │   └── data_validator.py    # Data validation
│   ├── api/                      # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py              # API entry point
│   │   ├── models.py            # Pydantic models
│   │   ├── routes/              # API routes
│   │   └── services/            # Business logic
│   └── analytics/                # Analytics modules
│       ├── __init__.py
│       └── metrics.py
├── config/                        # Configuration files
│   ├── database.py               # Database config
│   └── settings.py               # Application settings
├── notebooks/                     # Jupyter notebooks
│   └── exploratory_analysis.ipynb
├── tests/                         # Test suite
│   ├── test_etl.py
│   ├── test_api.py
│   └── test_queries.py
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
└── README.md                      # Project README
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- 8GB RAM minimum
- 5GB free disk space

### Installation

1. **Clone and navigate to project:**

   ```bash
   cd Yellow_Taxi_Trips_Analytics
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**

   ```bash
   sudo systemctl start postgresql
   sudo -u postgres psql
   ```

   In PostgreSQL:

   ```sql
   CREATE DATABASE city_rides_db;
   CREATE USER rides_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE city_rides_db TO rides_user;
   \q
   ```

5. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. **Initialize database schema:**

   ```bash
   psql -U rides_user -d city_rides_db -f sql/schema.sql
   ```

7. **Run ETL pipeline:**

   ```bash
   python src/etl/load_data.py
   ```

8. **Start API server (optional):**

   ```bash
   uvicorn src.api.main:app --reload
   ```

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and configuration
- **[Database Documentation](DATABASE.md)** - Schema, tables, and queries
- **[API Documentation](API.md)** - API endpoints and usage
- **[Analytics Guide](ANALYTICS.md)** - Data analysis and insights

## 🎯 Project Phases

### Phase 1: Foundation ✅

- [x] PostgreSQL database setup
- [x] Schema design with proper indexing
- [x] ETL pipeline implementation
- [ ] Load initial dataset (100k rows)

### Phase 2: Analysis 🔄

- [ ] Basic analytics queries
- [ ] Advanced analytics (window functions, CTEs)
- [ ] Performance optimization
- [ ] Materialized views

### Phase 3: API Layer 📋

- [ ] FastAPI setup
- [ ] CRUD endpoints
- [ ] Analytics endpoints
- [ ] Authentication

### Phase 4: Visualization 📊

- [ ] Dashboard design
- [ ] Metabase/Superset integration
- [ ] Interactive filters
- [ ] Real-time metrics

### Phase 5: Optimization 🚀

- [ ] Query optimization with EXPLAIN ANALYZE
- [ ] Advanced indexing strategies
- [ ] Caching layer
- [ ] Performance monitoring

## 🔑 Key Features

### Analytics Capabilities

- Average fare per distance/time
- Peak hours analysis by day of week
- Top pickup/dropoff zones
- Vendor performance metrics
- Revenue trends
- Trip duration patterns

### Technical Features

- Batch data loading (COPY/psycopg2)
- Optimized indexing (B-tree, GIN)
- Window functions for ranking
- Time-series rollups
- Materialized views for reports
- RESTful API with FastAPI

## 🛠️ Technologies

- **Database:** PostgreSQL 14+
- **ETL:** Python 3.9+, Pandas, PyArrow
- **API:** FastAPI, Uvicorn
- **ORM:** SQLAlchemy
- **Visualization:** Metabase/Superset (optional)
- **Testing:** pytest
- **Version Control:** Git

## 📈 Performance Targets

- Query response time: < 1ms with materialized views (achieved: 0.11ms avg)
- API latency: < 10ms for analytics endpoints (achieved: 3-7ms)
- ETL throughput: > 10k rows/second (achieved at scale)
- Database size: 4.56 GB for 17.4M rows
- MV refresh time: < 60s (achieved: 50.56s for all 9 views)
- Incremental refresh: < 10s for hot data (achieved: 5.49s)

## 🤝 Contributing

When contributing to this project:

1. Follow the existing code structure
2. Write unit tests for new features
3. Update documentation accordingly
4. Use meaningful commit messages
5. Optimize SQL queries before committing

## 📝 Notes

- Start with 100k rows for development/testing
- Use `EXPLAIN ANALYZE` for query optimization
- Always backup database before major changes
- Monitor disk space when loading full dataset
- Use connection pooling for API

## 🐛 Troubleshooting

Common issues and solutions are documented in [SETUP.md](SETUP.md#troubleshooting).

## 📞 Support

For questions or issues:

1. Check documentation in `docs/human/`
2. Review SQL queries in `sql/queries/`
3. Examine ETL logs for data loading issues

---

**Last Updated:** November 2, 2025
**Version:** 0.1.0
**Status:** In Development
