-- check: Target has no records that do not exist in source
-- severity: High
-- why: Records with no source counterpart are test data, leftovers from earlier runs, or broken keys.
SELECT 'customers' AS table_name, t.id AS target_id, t.legacy_id
FROM tgt.customers t
LEFT JOIN src.customers s ON s.customer_id = t.legacy_id
WHERE s.customer_id IS NULL
UNION ALL
SELECT 'orders', t.id, t.legacy_id
FROM tgt.orders t
LEFT JOIN src.orders s ON s.order_id = t.legacy_id
WHERE s.order_id IS NULL;
