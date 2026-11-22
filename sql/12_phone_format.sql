-- check: Migrated phones are in E.164 format (+380XXXXXXXXX)
-- severity: Low
-- why: The new platform's SMS provider accepts E.164 only.
SELECT id, legacy_id, phone
FROM tgt.customers
WHERE phone IS NOT NULL
  AND phone NOT GLOB '+380[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]';
