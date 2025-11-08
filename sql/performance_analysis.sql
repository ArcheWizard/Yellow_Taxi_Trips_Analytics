-- Query Performance Analysis and Optimization
-- City Rides Analytics Dashboard
-- Created: November 8, 2025

-- ====================
-- 1. EXPLAIN ANALYZE EXAMPLES
-- ====================

-- Compare query performance: Direct query vs Materialized View

-- Direct query (slower - scans full table)
EXPLAIN ANALYZE
SELECT
    z.borough,
    z.zone,
    COUNT(*) as pickup_count,
    ROUND(AVG(r.trip_distance)::numeric, 2) as avg_distance,
    ROUND(AVG(r.total_amount)::numeric, 2) as avg_fare
FROM rides r
LEFT JOIN zones z ON r.pickup_location_id = z.location_id
WHERE r.total_amount > 0
AND z.zone IS NOT NULL
GROUP BY z.borough, z.zone
ORDER BY pickup_count DESC
LIMIT 10;

-- Materialized view query (faster - pre-aggregated)
EXPLAIN ANALYZE
SELECT
    borough,
    zone,
    pickup_count,
    avg_distance,
    avg_fare
FROM mv_top_pickup_locations
WHERE zone IS NOT NULL
ORDER BY pickup_count DESC
LIMIT 10;

-- ====================
-- 2. INDEX USAGE ANALYSIS
-- ====================

-- Check which indexes are being used
SELECT
    schemaname,
    relname as tablename,
    indexrelname as indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find unused indexes (candidates for removal)
SELECT
    schemaname,
    relname as tablename,
    indexrelname as indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
AND idx_scan = 0
AND indexrelname NOT LIKE '%_pkey';

-- ====================
-- 3. TABLE SIZE ANALYSIS
-- ====================

-- Size of tables and indexes
SELECT
    t.schemaname,
    t.tablename,
    pg_size_pretty(pg_total_relation_size('"' || t.schemaname || '"."' || t.tablename || '"')) AS total_size,
    pg_size_pretty(pg_relation_size('"' || t.schemaname || '"."' || t.tablename || '"')) AS table_size,
    pg_size_pretty(pg_total_relation_size('"' || t.schemaname || '"."' || t.tablename || '"') -
                   pg_relation_size('"' || t.schemaname || '"."' || t.tablename || '"')) AS indexes_size
FROM pg_tables t
WHERE t.schemaname = 'public'
ORDER BY pg_total_relation_size('"' || t.schemaname || '"."' || t.tablename || '"') DESC;

-- Materialized view sizes
SELECT
    mv.schemaname,
    mv.matviewname,
    pg_size_pretty(pg_total_relation_size('"' || mv.schemaname || '"."' || mv.matviewname || '"')) AS size
FROM pg_matviews mv
WHERE mv.schemaname = 'public'
ORDER BY pg_total_relation_size('"' || mv.schemaname || '"."' || mv.matviewname || '"') DESC;

-- ====================
-- 4. QUERY STATISTICS
-- ====================

-- Most time-consuming queries (if pg_stat_statements is enabled)
-- Uncomment to use:
-- SELECT
--     query,
--     calls,
--     total_exec_time,
--     mean_exec_time,
--     max_exec_time
-- FROM pg_stat_statements
-- WHERE query NOT LIKE '%pg_stat_statements%'
-- ORDER BY total_exec_time DESC
-- LIMIT 10;

-- ====================
-- 5. VACUUM ANALYSIS
-- ====================

-- Check when tables were last vacuumed/analyzed
SELECT
    schemaname,
    relname,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY relname;

-- ====================
-- 6. MISSING INDEX RECOMMENDATIONS
-- ====================

-- Identify sequential scans that might benefit from indexes
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    ROUND(seq_tup_read::numeric / NULLIF(seq_scan, 0), 2) as avg_tuples_per_scan
FROM pg_stat_user_tables
WHERE schemaname = 'public'
AND seq_scan > 0
ORDER BY seq_tup_read DESC;

-- ====================
-- 7. CACHE HIT RATIO
-- ====================

-- Database cache hit ratio (should be > 99%)
SELECT
    'Cache Hit Ratio' as metric,
    ROUND((sum(blks_hit) * 100.0 / NULLIF(sum(blks_hit) + sum(blks_read), 0)), 2) as percentage
FROM pg_stat_database
WHERE datname = current_database();

-- Table-level cache hit ratios
SELECT
    schemaname,
    tablename,
    ROUND((heap_blks_hit * 100.0 / NULLIF(heap_blks_hit + heap_blks_read, 0)), 2) as cache_hit_ratio,
    heap_blks_read as disk_reads,
    heap_blks_hit as cache_hits
FROM pg_statio_user_tables
WHERE schemaname = 'public'
ORDER BY heap_blks_read DESC;

-- ====================
-- 8. CONNECTION AND ACTIVITY
-- ====================

-- Current database connections
SELECT
    datname,
    count(*) as connections,
    max(backend_start) as last_connection
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname;

-- Active queries
SELECT
    pid,
    usename,
    state,
    query_start,
    EXTRACT(EPOCH FROM (now() - query_start)) as seconds_running,
    LEFT(query, 100) as query_preview
FROM pg_stat_activity
WHERE state = 'active'
AND pid != pg_backend_pid()
ORDER BY query_start;

-- ====================
-- 9. OPTIMIZATION RECOMMENDATIONS
-- ====================

-- Summary report
DO $$
DECLARE
    rides_count bigint;
    total_size text;
    cache_ratio numeric;
BEGIN
    -- Get statistics
    SELECT COUNT(*) INTO rides_count FROM rides;
    SELECT pg_size_pretty(pg_total_relation_size('rides')) INTO total_size;
    SELECT ROUND((sum(blks_hit) * 100.0 / NULLIF(sum(blks_hit) + sum(blks_read), 0)), 2)
    INTO cache_ratio
    FROM pg_stat_database
    WHERE datname = current_database();

    -- Print report
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'DATABASE PERFORMANCE SUMMARY';
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Total Rides: %', rides_count;
    RAISE NOTICE 'Rides Table Size: %', total_size;
    RAISE NOTICE 'Cache Hit Ratio: %%', cache_ratio;
    RAISE NOTICE '';
    RAISE NOTICE 'RECOMMENDATIONS:';

    IF cache_ratio < 95 THEN
        RAISE NOTICE '  ⚠ Cache hit ratio is low. Consider increasing shared_buffers.';
    ELSE
        RAISE NOTICE '  ✓ Cache hit ratio is good.';
    END IF;

    RAISE NOTICE '  ✓ Use materialized views for frequently accessed aggregations.';
    RAISE NOTICE '  ✓ Run VACUUM ANALYZE regularly to update statistics.';
    RAISE NOTICE '  ✓ Monitor slow queries with EXPLAIN ANALYZE.';
    RAISE NOTICE '==========================================';
END $$;
