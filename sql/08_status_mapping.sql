-- check: Order statuses follow the mapping spec
-- severity: High
-- why: A wrong status changes business meaning (e.g. a refunded order counted as revenue).
WITH mapping(legacy_status, expected_status) AS (
    VALUES ('NEW', 'new'), ('PAID', 'paid'), ('SHIPPED', 'shipped'),
           ('CANCELED', 'cancelled'), ('REFUNDED', 'refunded')
)
SELECT s.status AS legacy_status,
       m.expected_status,
       t.status AS actual_status,
       COUNT(*) AS orders
FROM src.orders s
JOIN tgt.orders t ON t.legacy_id = s.order_id
LEFT JOIN mapping m ON m.legacy_status = s.status
WHERE m.expected_status IS NULL OR t.status <> m.expected_status
GROUP BY s.status, m.expected_status, t.status;
