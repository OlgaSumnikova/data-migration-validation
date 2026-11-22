-- check: full_name is split into first_name + last_name without data loss
-- severity: Medium
-- why: Truncated names break invoices, shipping labels and personalised emails. Look at the length of the affected values.
SELECT DISTINCT s.customer_id,
       s.full_name,
       t.first_name,
       t.last_name,
       LENGTH(s.full_name) - LENGTH(t.first_name) - 1 AS source_last_name_length
FROM src.customers s
JOIN tgt.customers t ON t.legacy_id = s.customer_id
WHERE t.first_name || ' ' || t.last_name <> s.full_name
ORDER BY s.customer_id;
