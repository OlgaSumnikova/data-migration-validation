-- check: Orders are linked to the same customer as in source
-- severity: Critical
-- why: An order attached to the wrong customer is both a data and a privacy problem.
SELECT s.order_id, s.customer_id AS source_customer_id, c.legacy_id AS target_customer_legacy_id
FROM src.orders s
JOIN tgt.orders o ON o.legacy_id = s.order_id
JOIN tgt.customers c ON c.id = o.customer_id
WHERE c.legacy_id <> s.customer_id
ORDER BY s.order_id;
