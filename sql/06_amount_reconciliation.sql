-- check: Order totals reconcile per currency
-- severity: Critical
-- why: Finance will compare totals first. Any difference must be explained down to the row level.
WITH s AS (
    SELECT currency, COUNT(*) AS n, SUM(amount_cents) / 100.0 AS total
    FROM src.orders GROUP BY currency
), t AS (
    SELECT currency, COUNT(*) AS n, ROUND(SUM(total), 2) AS total
    FROM tgt.orders GROUP BY currency
)
SELECT s.currency,
       s.n AS source_orders, t.n AS target_orders,
       s.total AS source_total, t.total AS target_total,
       ROUND(COALESCE(t.total, 0) - s.total, 2) AS diff
FROM s
LEFT JOIN t ON t.currency = s.currency
WHERE t.total IS NULL OR ABS(t.total - s.total) > 0.005
ORDER BY s.currency;
