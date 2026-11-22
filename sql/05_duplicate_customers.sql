-- check: No duplicated customers in target
-- severity: High
-- why: Duplicates split order history between two accounts and break login by email. Typical cause: a retried batch without an idempotency key.
SELECT legacy_id, COUNT(*) AS copies, GROUP_CONCAT(id) AS target_ids
FROM tgt.customers
GROUP BY legacy_id
HAVING COUNT(*) > 1
ORDER BY legacy_id;
