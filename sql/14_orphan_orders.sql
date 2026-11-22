-- check: Every order belongs to an existing customer
-- severity: Critical
-- why: Orphaned orders are invisible in the customer account and break reports that join orders to customers.
SELECT o.id AS target_order_id, o.legacy_id AS legacy_order_id, o.customer_id,
       s.customer_id AS source_customer_id
FROM tgt.orders o
LEFT JOIN tgt.customers c ON c.id = o.customer_id
JOIN src.orders s ON s.order_id = o.legacy_id
WHERE c.id IS NULL
ORDER BY o.legacy_id;
