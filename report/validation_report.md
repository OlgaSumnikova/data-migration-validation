# Data Migration Validation Report

Generated: 2026-11-22 22:06  
Checks run: 15 | Passed: 4 | Failed: 11

## Summary

| # | Check | Severity | Result | Problem rows |
|---|---|---|---|---|
| 1 | Row counts match between source and target | Critical | ❌ FAIL | 2 |
| 2 | Every source customer exists in target | Critical | ❌ FAIL | 3 |
| 3 | Every source order exists in target | Critical | ❌ FAIL | 12 |
| 4 | Target has no records that do not exist in source | High | ✅ PASS | 0 |
| 5 | No duplicated customers in target | High | ❌ FAIL | 4 |
| 6 | Order totals reconcile per currency | Critical | ❌ FAIL | 3 |
| 7 | Each migrated order keeps its exact amount | Critical | ❌ FAIL | 30 |
| 8 | Order statuses follow the mapping spec | High | ❌ FAIL | 1 |
| 9 | full_name is split into first_name + last_name without data loss | Medium | ❌ FAIL | 69 |
| 10 | Registration dates converted from DD.MM.YYYY to ISO correctly | High | ❌ FAIL | 22 |
| 11 | Phones present in source are not lost in target | Medium | ❌ FAIL | 48 |
| 12 | Migrated phones are in E.164 format (+380XXXXXXXXX) | Low | ✅ PASS | 0 |
| 13 | Emails are trimmed and lower-cased as per spec | Medium | ✅ PASS | 0 |
| 14 | Every order belongs to an existing customer | Critical | ❌ FAIL | 6 |
| 15 | Orders are linked to the same customer as in source | Critical | ✅ PASS | 0 |

## Failed checks

### Row counts match between source and target

**Severity:** Critical  
**Why it matters:** The most basic completeness check. Note: a near-match can still hide lost AND duplicated rows that cancel each other out.  
**Query:** [`sql/01_row_counts.sql`](../sql/01_row_counts.sql)  
**Problem rows:** 2

| table_name | source_count | target_count | diff |
|---|---|---|---|
| customers | 500 | 501 | 1 |
| orders | 2000 | 1988 | -12 |

### Every source customer exists in target

**Severity:** Critical  
**Why it matters:** Lost customers mean lost accounts and order history, and orphaned orders downstream.  
**Query:** [`sql/02_missing_customers.sql`](../sql/02_missing_customers.sql)  
**Problem rows:** 3

| customer_id | full_name | email |
|---|---|---|
| 23 | Iryna Smith | customer23@gmail.com |
| 92 | Andrii Melnyk |  customer92@gmail.com  |
| 424 | Maria Tkachenko | Customer424@gmail.com |

### Every source order exists in target

**Severity:** Critical  
**Why it matters:** Lost orders mean lost revenue records. Consecutive IDs usually point to a failed batch.  
**Query:** [`sql/03_missing_orders.sql`](../sql/03_missing_orders.sql)  
**Problem rows:** 12 (showing first 10)

| order_id | customer_id | amount | currency | status |
|---|---|---|---|---|
| 1501 | 9 | 409.53 | EUR | SHIPPED |
| 1502 | 187 | 167.60 | UAH | PAID |
| 1503 | 463 | 17.35 | UAH | CANCELED |
| 1504 | 333 | 158.49 | EUR | PAID |
| 1505 | 173 | 28.50 | UAH | REFUNDED |
| 1506 | 235 | 434.14 | UAH | SHIPPED |
| 1507 | 447 | 411.04 | UAH | SHIPPED |
| 1508 | 195 | 132.82 | USD | PAID |
| 1509 | 356 | 442.32 | UAH | PAID |
| 1510 | 412 | 337.91 | EUR | SHIPPED |

### No duplicated customers in target

**Severity:** High  
**Why it matters:** Duplicates split order history between two accounts and break login by email. Typical cause: a retried batch without an idempotency key.  
**Query:** [`sql/05_duplicate_customers.sql`](../sql/05_duplicate_customers.sql)  
**Problem rows:** 4

| legacy_id | copies | target_ids |
|---|---|---|
| 221 | 2 | 219,220 |
| 254 | 2 | 253,254 |
| 433 | 2 | 432,433 |
| 439 | 2 | 439,440 |

### Order totals reconcile per currency

**Severity:** Critical  
**Why it matters:** Finance will compare totals first. Any difference must be explained down to the row level.  
**Query:** [`sql/06_amount_reconciliation.sql`](../sql/06_amount_reconciliation.sql)  
**Problem rows:** 3

| currency | source_orders | target_orders | source_total | target_total | diff |
|---|---|---|---|---|---|
| EUR | 417 | 414 | 108471.57 | 107561.77 | -909.80 |
| UAH | 1365 | 1357 | 343216.15 | 341349.08 | -1867.07 |
| USD | 218 | 217 | 55127.50 | 54992.82 | -134.68 |

### Each migrated order keeps its exact amount

**Severity:** Critical  
**Why it matters:** Finds the rows behind a reconciliation gap. Diffs under 1.00 that always go negative suggest truncation in the cents conversion.  
**Query:** [`sql/07_amount_row_level.sql`](../sql/07_amount_row_level.sql)  
**Problem rows:** 30 (showing first 10)

| order_id | source_amount | target_amount | diff | currency |
|---|---|---|---|---|
| 62 | 292.37 | 292.00 | -0.37 | EUR |
| 68 | 136.86 | 136.00 | -0.86 | UAH |
| 147 | 133.88 | 133.00 | -0.88 | EUR |
| 166 | 99.35 | 99.00 | -0.35 | UAH |
| 185 | 464.43 | 464.00 | -0.43 | UAH |
| 290 | 262.60 | 262.00 | -0.60 | EUR |
| 306 | 494.68 | 494.00 | -0.68 | USD |
| 343 | 24.49 | 24.00 | -0.49 | UAH |
| 426 | 201.75 | 201.00 | -0.75 | USD |
| 457 | 28.78 | 28.00 | -0.78 | UAH |

### Order statuses follow the mapping spec

**Severity:** High  
**Why it matters:** A wrong status changes business meaning (e.g. a refunded order counted as revenue).  
**Query:** [`sql/08_status_mapping.sql`](../sql/08_status_mapping.sql)  
**Problem rows:** 1

| legacy_status | expected_status | actual_status | orders |
|---|---|---|---|
| REFUNDED | refunded | paid | 108 |

### full_name is split into first_name + last_name without data loss

**Severity:** Medium  
**Why it matters:** Truncated names break invoices, shipping labels and personalised emails. Look at the length of the affected values.  
**Query:** [`sql/09_name_split.sql`](../sql/09_name_split.sql)  
**Problem rows:** 69 (showing first 10)

| customer_id | full_name | first_name | last_name | source_last_name_length |
|---|---|---|---|---|
| 6 | Sofia Van der Westhuizen-Smit | Sofia | Van der Westhuizen-S | 23 |
| 7 | Lukas Van der Westhuizen-Smit | Lukas | Van der Westhuizen-S | 23 |
| 20 | Ivan Van der Westhuizen-Smit | Ivan | Van der Westhuizen-S | 23 |
| 24 | Iryna Van der Westhuizen-Smit | Iryna | Van der Westhuizen-S | 23 |
| 25 | Andrii Kovalchuk-Dombrovskyi | Andrii | Kovalchuk-Dombrovsky | 21 |
| 32 | Olena Van der Westhuizen-Smit | Olena | Van der Westhuizen-S | 23 |
| 60 | Maksym Kovalchuk-Dombrovskyi | Maksym | Kovalchuk-Dombrovsky | 21 |
| 63 | Kateryna Kovalchuk-Dombrovskyi | Kateryna | Kovalchuk-Dombrovsky | 21 |
| 66 | Chloé Van der Westhuizen-Smit | Chloé | Van der Westhuizen-S | 23 |
| 69 | Maria Van der Westhuizen-Smit | Maria | Van der Westhuizen-S | 23 |

### Registration dates converted from DD.MM.YYYY to ISO correctly

**Severity:** High  
**Why it matters:** Wrong dates break cohort reports, loyalty rules and data retention. Day and month swapped only when day <= 12 is a classic parsing bug.  
**Query:** [`sql/10_registration_date.sql`](../sql/10_registration_date.sql)  
**Problem rows:** 22 (showing first 10)

| customer_id | source_value | expected_iso | actual_iso |
|---|---|---|---|
| 302 | 04.06.2026 | 2026-06-04 | 2026-04-06 |
| 307 | 09.05.2022 | 2022-05-09 | 2022-09-05 |
| 312 | 11.03.2024 | 2024-03-11 | 2024-11-03 |
| 315 | 09.08.2021 | 2021-08-09 | 2021-09-08 |
| 316 | 02.06.2022 | 2022-06-02 | 2022-02-06 |
| 319 | 06.08.2023 | 2023-08-06 | 2023-06-08 |
| 321 | 06.08.2024 | 2024-08-06 | 2024-06-08 |
| 322 | 01.11.2024 | 2024-11-01 | 2024-01-11 |
| 324 | 04.05.2023 | 2023-05-04 | 2023-04-05 |
| 325 | 02.08.2021 | 2021-08-02 | 2021-02-08 |

### Phones present in source are not lost in target

**Severity:** Medium  
**Why it matters:** Lost phones break delivery notifications and 2FA. Look at which source formats are affected.  
**Query:** [`sql/11_phone_lost.sql`](../sql/11_phone_lost.sql)  
**Problem rows:** 48 (showing first 10)

| customer_id | source_phone | target_phone |
|---|---|---|
| 42 | (097) 572-62-84 | NULL |
| 52 | (066) 421-02-49 | NULL |
| 61 | (067) 270-28-95 | NULL |
| 104 | (093) 188-88-80 | NULL |
| 113 | (063) 715-51-88 | NULL |
| 125 | (097) 025-78-72 | NULL |
| 136 | (097) 205-49-32 | NULL |
| 140 | (063) 883-98-22 | NULL |
| 148 | (093) 287-33-42 | NULL |
| 154 | (050) 080-10-06 | NULL |

### Every order belongs to an existing customer

**Severity:** Critical  
**Why it matters:** Orphaned orders are invisible in the customer account and break reports that join orders to customers.  
**Query:** [`sql/14_orphan_orders.sql`](../sql/14_orphan_orders.sql)  
**Problem rows:** 6

| target_order_id | legacy_order_id | customer_id | source_customer_id |
|---|---|---|---|
| 102 | 102 | NULL | 424 |
| 156 | 156 | NULL | 23 |
| 158 | 158 | NULL | 92 |
| 171 | 171 | NULL | 92 |
| 246 | 246 | NULL | 23 |
| 1791 | 1803 | NULL | 23 |
