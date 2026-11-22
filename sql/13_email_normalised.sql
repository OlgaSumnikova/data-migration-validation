-- check: Emails are trimmed and lower-cased as per spec
-- severity: Medium
-- why: Email is the login. Case or whitespace differences create "user not found" errors and duplicates.
SELECT DISTINCT s.customer_id, s.email AS source_email, t.email AS target_email
FROM src.customers s
JOIN tgt.customers t ON t.legacy_id = s.customer_id
WHERE t.email <> LOWER(TRIM(s.email))
ORDER BY s.customer_id;
