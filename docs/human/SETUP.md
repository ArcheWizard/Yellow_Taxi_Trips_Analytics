# Setup Guide - City Rides Analytics Dashboard

## 📋 Prerequisites

### System Requirements

- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **RAM:** 8GB minimum, 16GB recommended
- **Disk Space:** 5GB free space
- **CPU:** 4+ cores recommended

### Software Requirements

- Python 3.9 or higher
- PostgreSQL 14 or higher
- Git
- pip (Python package manager)

## 🔧 Detailed Installation

### Step 1: PostgreSQL Installation

#### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

#### macOS

```bash
# Using Homebrew
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Verify installation
psql --version
```

#### Verify PostgreSQL is Running

```bash
sudo systemctl status postgresql
```

### Step 2: Database Setup

#### Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql
```

Inside PostgreSQL prompt:

```sql
-- Create database
CREATE DATABASE city_rides_db;

-- Create user with password
CREATE USER rides_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE city_rides_db TO rides_user;

-- Grant schema privileges
\c city_rides_db
GRANT ALL ON SCHEMA public TO rides_user;

-- Exit
\q
```

#### Test Connection

```bash
psql -U rides_user -d city_rides_db -h localhost
```

If prompted for password, enter the password you set above.

### Step 3: Python Environment Setup

#### Create Virtual Environment

```bash
cd Yellow_Taxi_Trips_Analytics

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows
```

#### Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install psycopg2-binary==2.9.9
pip install pandas==2.1.4
pip install pyarrow==14.0.1
pip install python-dotenv==1.0.0
pip install sqlalchemy==2.0.23
pip install fastapi==0.104.1
pip install uvicorn==0.24.0

# Save to requirements.txt
pip freeze > requirements.txt
```

### Step 4: Environment Configuration

#### Create .env File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

#### .env File Contents

```ini
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=city_rides_db
DB_USER=rides_user
DB_PASSWORD=your_secure_password

# API Configuration (for future use)
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# ETL Configuration
BATCH_SIZE=1000
SAMPLE_SIZE=100000

# Logging
LOG_LEVEL=INFO
```

### Step 5: Project Structure Setup

#### Create Directory Structure

```bash
# Create main directories
mkdir -p data
mkdir -p sql/queries
mkdir -p src/etl
mkdir -p src/api/routes
mkdir -p src/api/services
mkdir -p src/analytics
mkdir -p config
mkdir -p notebooks
mkdir -p tests
mkdir -p logs

# Create __init__.py files for Python packages
touch src/__init__.py
touch src/etl/__init__.py
touch src/api/__init__.py
touch src/api/routes/__init__.py
touch src/api/services/__init__.py
touch src/analytics/__init__.py
touch config/__init__.py
```

#### Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Data files
data/
*.parquet
*.csv
*.json
!sql/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db

# Jupyter Notebooks
.ipynb_checkpoints/
*.ipynb_checkpoints

# Coverage
.coverage
htmlcov/
EOF
```

### Step 6: Database Schema Initialization

#### Apply Schema

```bash
# Initialize database schema
psql -U rides_user -d city_rides_db -h localhost -f sql/schema.sql
```

#### Verify Tables Created

```bash
psql -U rides_user -d city_rides_db -h localhost -c "\dt"
```

Expected output:

```text
         List of relations
 Schema |  Name   | Type  |   Owner
--------+---------+-------+------------
 public | rides   | table | rides_user
 public | vendors | table | rides_user
 public | zones   | table | rides_user
```

### Step 7: Download Dataset

#### Using wget

```bash
cd data

# Download November 2024 dataset
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-11.parquet

# Verify download
ls -lh yellow_tripdata_2024-11.parquet
```

#### Using curl (alternative)

```bash
curl -o data/yellow_tripdata_2024-11.parquet \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-11.parquet
```

### Step 8: Run ETL Pipeline

#### Test Run (100k rows)

```bash
# Activate virtual environment if not already active
source venv/bin/activate

# Run ETL with sample
python src/etl/load_data.py
```

#### Full Load (after testing)

Edit `src/etl/load_data.py` and change:

```python
loader.run_etl(file_path, sample_size=100000)  # Sample
```

to:

```python
loader.run_etl(file_path)  # Full dataset
```

### Step 9: Verify Data Load

#### Check Row Count

```bash
psql -U rides_user -d city_rides_db -h localhost -c "SELECT COUNT(*) FROM rides;"
```

#### View Sample Data

```bash
psql -U rides_user -d city_rides_db -h localhost -c "SELECT * FROM rides LIMIT 5;"
```

#### Check Database Size

```bash
psql -U rides_user -d city_rides_db -h localhost -c "
SELECT
    pg_size_pretty(pg_database_size('city_rides_db')) as database_size;
"
```

## 🔍 Verification Checklist

- [ ] PostgreSQL installed and running
- [ ] Database `city_rides_db` created
- [ ] User `rides_user` created with proper privileges
- [ ] Python virtual environment created and activated
- [ ] All Python dependencies installed
- [ ] `.env` file configured with correct credentials
- [ ] Database schema applied successfully
- [ ] Tables created (rides, vendors, zones)
- [ ] Indexes created
- [ ] Dataset downloaded to `data/` folder
- [ ] ETL pipeline runs without errors
- [ ] Data visible in database
- [ ] Sample queries return results

## 🐛 Troubleshooting

### PostgreSQL Connection Issues

**Problem:** `psql: error: connection to server on socket failed`

**Solution:**

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql

# Check port 5432
sudo netstat -plnt | grep 5432
```

**Problem:** `FATAL: password authentication failed`

**Solution:**
Edit PostgreSQL configuration:

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Change this line:

```text
local   all             all                                     peer
```

to:

```text
local   all             all                                     md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### Python Issues

**Problem:** `ModuleNotFoundError: No module named 'psycopg2'`

**Solution:**

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall psycopg2
pip install psycopg2-binary
```

**Problem:** `ImportError: cannot import name 'DatabaseConfig'`

**Solution:**

```bash
# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Yellow_Taxi_Trips_Analytics"

# Or run from project root
cd /path/to/Yellow_Taxi_Trips_Analytics
python src/etl/load_data.py
```

### ETL Issues

**Problem:** `FileNotFoundError: data/yellow_tripdata_2024-11.parquet`

**Solution:**

```bash
# Ensure file exists
ls -lh data/yellow_tripdata_2024-11.parquet

# Download if missing
wget -P data/ https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-11.parquet
```

**Problem:** `Memory error during data loading`

**Solution:**
Reduce sample size in `load_data.py`:

```python
loader.run_etl(file_path, sample_size=50000)  # Reduce from 100k
```

### Database Issues

**Problem:** `ERROR: relation "rides" does not exist`

**Solution:**

```bash
# Reapply schema
psql -U rides_user -d city_rides_db -h localhost -f sql/schema.sql
```

**Problem:** Slow query performance

**Solution:**

```bash
# Check if indexes exist
psql -U rides_user -d city_rides_db -h localhost -c "\di"

# Analyze tables for statistics
psql -U rides_user -d city_rides_db -h localhost -c "ANALYZE rides;"
```

## 🔐 Security Best Practices

1. **Never commit `.env` file to Git**
2. **Use strong passwords** (16+ characters, mixed case, numbers, symbols)
3. **Limit database user privileges** to only what's needed
4. **Keep PostgreSQL updated** with security patches
5. **Use SSL/TLS** for production database connections
6. **Regularly backup** your database

## 📝 Next Steps

After successful setup:

1. Review [DATABASE.md](DATABASE.md) for schema details
2. Explore sample queries in `sql/queries/`
3. Run basic analytics queries
4. Set up API layer (optional)
5. Connect visualization tools (optional)

## 🔄 Updating

### Update Python Dependencies

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Update PostgreSQL

```bash
sudo apt update
sudo apt upgrade postgresql
```

### Pull Latest Code Changes

```bash
git pull origin main
```

---

**Need Help?** Check the troubleshooting section or review the documentation in `docs/human/`.
