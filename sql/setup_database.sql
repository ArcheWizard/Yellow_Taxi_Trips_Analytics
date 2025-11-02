-- Database and User Setup Script
-- This script creates the database and user for the City Rides Analytics project

-- Create the database
CREATE DATABASE city_rides_db;

-- Create the user
CREATE USER rides_user WITH PASSWORD 'your_secure_password';

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE city_rides_db TO rides_user;

-- Connect to the new database
\c city_rides_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO rides_user;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO rides_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO rides_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO rides_user;
