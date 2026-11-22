-- check: Every source customer exists in target
-- severity: Critical
-- why: Lost customers mean lost accounts and order history, and orphaned orders downstream.
SELECT s.customer_id, s.full_name, s.email
FROM src.customers s
LEFT JOIN tgt.customers t ON t.legacy_id = s.customer_id
WHERE t.id IS NULL
ORDER BY s.customer_id;
