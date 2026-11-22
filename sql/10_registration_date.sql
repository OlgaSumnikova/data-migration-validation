-- check: Registration dates converted from DD.MM.YYYY to ISO correctly
-- severity: High
-- why: Wrong dates break cohort reports, loyalty rules and data retention. Day and month swapped only when day <= 12 is a classic parsing bug.
WITH compared AS (
    SELECT s.customer_id,
           s.created_at AS source_value,
           substr(s.created_at, 7, 4) || '-' || substr(s.created_at, 4, 2) || '-' || substr(s.created_at, 1, 2) AS expected_iso,
           t.created_at AS actual_iso
    FROM src.customers s
    JOIN tgt.customers t ON t.legacy_id = s.customer_id
)
SELECT DISTINCT customer_id, source_value, expected_iso, actual_iso
FROM compared
WHERE actual_iso <> expected_iso
ORDER BY customer_id;
