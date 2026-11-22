-- check: Row counts match between source and target
-- severity: Critical
-- why: The most basic completeness check. Note: a near-match can still hide lost AND duplicated rows that cancel each other out.
WITH counts AS (
    SELECT 'customers' AS table_name,
           (SELECT COUNT(*) FROM src.customers) AS source_count,
           (SELECT COUNT(*) FROM tgt.customers) AS target_count
    UNION ALL
    SELECT 'orders',
           (SELECT COUNT(*) FROM src.orders),
           (SELECT COUNT(*) FROM tgt.orders)
)
SELECT table_name, source_count, target_count, target_count - source_count AS diff
FROM counts
WHERE source_count <> target_count;
