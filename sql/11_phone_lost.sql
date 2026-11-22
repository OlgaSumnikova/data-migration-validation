-- check: Phones present in source are not lost in target
-- severity: Medium
-- why: Lost phones break delivery notifications and 2FA. Look at which source formats are affected.
SELECT DISTINCT s.customer_id, s.phone AS source_phone, t.phone AS target_phone
FROM src.customers s
JOIN tgt.customers t ON t.legacy_id = s.customer_id
WHERE s.phone IS NOT NULL AND TRIM(s.phone) <> '' AND t.phone IS NULL
ORDER BY s.customer_id;
