-- check: Every source order exists in target
-- severity: Critical
-- why: Lost orders mean lost revenue records. Consecutive IDs usually point to a failed batch.
SELECT s.order_id, s.customer_id, s.amount_cents / 100.0 AS amount, s.currency, s.status
FROM src.orders s
LEFT JOIN tgt.orders t ON t.legacy_id = s.order_id
WHERE t.id IS NULL
ORDER BY s.order_id;
