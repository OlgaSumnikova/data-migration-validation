-- check: Each migrated order keeps its exact amount
-- severity: Critical
-- why: Finds the rows behind a reconciliation gap. Diffs under 1.00 that always go negative suggest truncation in the cents conversion.
SELECT s.order_id,
       s.amount_cents / 100.0 AS source_amount,
       t.total AS target_amount,
       ROUND(t.total - s.amount_cents / 100.0, 2) AS diff,
       s.currency
FROM src.orders s
JOIN tgt.orders t ON t.legacy_id = s.order_id
WHERE CAST(ROUND(t.total * 100) AS INTEGER) <> s.amount_cents
ORDER BY s.order_id;
