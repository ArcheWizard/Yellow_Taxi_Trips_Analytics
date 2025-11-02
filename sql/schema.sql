-- City Rides Analytics Database Schema
-- PostgreSQL 14+
-- Created: November 2, 2025

-- Create extension for better indexing if needed
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Zones/Locations table
CREATE TABLE zones (
    location_id INTEGER PRIMARY KEY,
    borough VARCHAR(50),
    zone VARCHAR(100),
    service_zone VARCHAR(50)
);

COMMENT ON TABLE zones IS 'NYC taxi zones lookup table';
COMMENT ON COLUMN zones.location_id IS 'Unique zone identifier from TLC';
COMMENT ON COLUMN zones.borough IS 'NYC borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island)';
COMMENT ON COLUMN zones.zone IS 'Specific zone name';
COMMENT ON COLUMN zones.service_zone IS 'Service classification (Yellow Zone, Green Zone, etc.)';

-- Vendors table (simplified - TLC data doesn't have driver IDs, so we'll use vendor)
CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY,
    vendor_name VARCHAR(100)
);

COMMENT ON TABLE vendors IS 'Taxi vendor/company information';
COMMENT ON COLUMN vendors.vendor_id IS '1=Creative Mobile Technologies, 2=VeriFone Inc.';

-- Insert vendor data
INSERT INTO vendors (vendor_id, vendor_name) VALUES
(1, 'Creative Mobile Technologies'),
(2, 'VeriFone Inc.');

-- Rides table (main fact table)
CREATE TABLE rides (
    ride_id BIGSERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    pickup_datetime TIMESTAMP NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count INTEGER,
    trip_distance NUMERIC(8,2),
    pickup_location_id INTEGER REFERENCES zones(location_id),
    dropoff_location_id INTEGER REFERENCES zones(location_id),
    rate_code_id INTEGER,
    store_and_fwd_flag CHAR(1),
    payment_type INTEGER,
    fare_amount NUMERIC(8,2),
    extra NUMERIC(8,2),
    mta_tax NUMERIC(8,2),
    tip_amount NUMERIC(8,2),
    tolls_amount NUMERIC(8,2),
    improvement_surcharge NUMERIC(8,2),
    total_amount NUMERIC(8,2),
    congestion_surcharge NUMERIC(8,2),
    airport_fee NUMERIC(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE rides IS 'Main fact table for NYC Yellow Taxi trips';
COMMENT ON COLUMN rides.ride_id IS 'Auto-generated unique identifier';
COMMENT ON COLUMN rides.vendor_id IS 'Reference to vendors table';
COMMENT ON COLUMN rides.pickup_datetime IS 'When passenger was picked up';
COMMENT ON COLUMN rides.dropoff_datetime IS 'When passenger was dropped off';
COMMENT ON COLUMN rides.passenger_count IS 'Number of passengers (1-6)';
COMMENT ON COLUMN rides.trip_distance IS 'Distance in miles';
COMMENT ON COLUMN rides.rate_code_id IS '1=Standard, 2=JFK, 3=Newark, 4=Nassau/Westchester, 5=Negotiated, 6=Group';
COMMENT ON COLUMN rides.store_and_fwd_flag IS 'Y=stored before sending, N=not stored';
COMMENT ON COLUMN rides.payment_type IS '1=Credit card, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided';
COMMENT ON COLUMN rides.fare_amount IS 'Base time-and-distance fare';
COMMENT ON COLUMN rides.tip_amount IS 'Tip amount (credit card only)';
COMMENT ON COLUMN rides.total_amount IS 'Total amount charged to passenger';

-- Indexes for performance
CREATE INDEX idx_rides_pickup_datetime ON rides(pickup_datetime);
CREATE INDEX idx_rides_dropoff_datetime ON rides(dropoff_datetime);
CREATE INDEX idx_rides_pickup_location ON rides(pickup_location_id);
CREATE INDEX idx_rides_dropoff_location ON rides(dropoff_location_id);
CREATE INDEX idx_rides_vendor ON rides(vendor_id);

-- Composite index for common query patterns
CREATE INDEX idx_rides_datetime_location ON rides(pickup_datetime, pickup_location_id);

-- Display confirmation
SELECT 'Schema created successfully!' as status;
SELECT 'Tables created: ' || count(*) as tables FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
