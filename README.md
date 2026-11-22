# Data Migration Validation: SQL Reconciliation Case Study

A hands-on case study of validating a data migration with SQL: comparing a legacy e-commerce database with the migrated one, finding defects, and reporting them in a form a team can act on.

> **Note:** the data is synthetic. The migration script deliberately reproduces bugs that commonly show up in real migrations, so the checks have something real to find. No client data is used.

## The scenario

An online shop moves from a legacy system to a new platform. The data is transformed along the way:

| Legacy (source) | New platform (target) | Rule |
|---|---|---|
| `customers.full_name` | `first_name`, `last_name` | Split on the first space |
| `customers.email` | `email` | Trim + lower-case |
| `customers.phone` (mixed formats) | `phone` | Normalise to E.164 (`+380XXXXXXXXX`) |
| `created_at` as `DD.MM.YYYY` | `created_at` as ISO `YYYY-MM-DD` | Date format conversion |
| `orders.amount_cents` (integer) | `orders.total` (decimal) | Divide by 100, keep 2 decimals |
| `NEW / PAID / SHIPPED / CANCELED / REFUNDED` | `new / paid / shipped / cancelled / refunded` | Status mapping |
| `customer_id` | `customer_id` → new surrogate keys | Remap via `legacy_id` |

## Approach

The checks follow the usual layers of migration testing, from cheap and broad to detailed:

1. **Completeness:** row counts, missing records, unexpected extra records
2. **Uniqueness:** duplicates created by retries
3. **Accuracy:** aggregate reconciliation by currency, then row-level comparison to explain the gap
4. **Transformation rules:** every mapping rule from the spec checked against source values
5. **Referential integrity:** orphaned orders, orders linked to the wrong customer

Every check is a single SQL query that **returns the problem rows**: 0 rows = PASS. This keeps the rule simple and makes the output directly usable as bug evidence.

## Results

**15 checks: 4 passed, 11 failed.** Full report with sample rows: [`report/validation_report.md`](report/validation_report.md)

| # | Finding | Severity | Evidence | Likely root cause |
|---|---|---|---|---|
| 1 | Row count for customers is off by just +1, which hides 3 lost **and** 4 duplicated customers | — | checks 01, 02, 05 | A count check alone is not enough |
| 2 | 3 customers not migrated; their 6 orders are left without an owner | Critical | checks 02, 14 | Lookup failure, orders still inserted with `customer_id = NULL` |
| 3 | 12 orders with consecutive IDs 1501–1512 are missing | Critical | check 03 | One failed batch, not retried |
| 4 | 4 customers exist twice in target | High | check 05 | Batch retry without idempotency; no `UNIQUE` on `legacy_id` |
| 5 | Totals don't reconcile in all 3 currencies | Critical | check 06 | Explained by findings 3 and 6 |
| 6 | 30 orders lost their cents (e.g. 292.37 → 292.00) | Critical | check 07 | Integer division in the cents → decimal conversion |
| 7 | All 108 `REFUNDED` orders became `paid` | High | check 08 | Status missing from the mapping table, falls back to a default |
| 8 | Last names longer than 20 characters are truncated | Medium | check 09 | `VARCHAR(20)` in target truncates silently |
| 9 | Registration dates with day ≤ 12 have day and month swapped, in one ID range only | High | check 10 | One batch parsed `DD.MM` as `MM.DD` |
| 10 | Phones in `(0XX) XXX-XX-XX` format are lost (NULL) | Medium | check 11 | Normaliser only handles numbers starting with `+` |

What passed and is worth stating: no unexpected records, emails normalised correctly, all migrated phones in valid E.164 format, every linked order points to the right customer.

## How to run

Requires Python 3.9+. No external packages: only the standard library (`sqlite3`).

```bash
python generate_data.py   # creates data/legacy.db and data/target.db
python run_checks.py      # runs all checks, writes report/validation_report.md
```

`run_checks.py` exits with code `1` if any check fails, so it can run as a step in a CI pipeline.

To explore manually in DBeaver or any SQLite client, open a connection and attach both files:

```sql
ATTACH DATABASE 'data/legacy.db' AS src;
ATTACH DATABASE 'data/target.db' AS tgt;
```

Then any file in `sql/` can be run as is.

## Project structure

```
├── generate_data.py      # builds source data and runs the (buggy) migration
├── run_checks.py         # runs every check in sql/ and writes the report
├── sql/                  # one validation check per file, with severity and rationale in the header
├── data/                 # legacy.db (source) and target.db (migrated)
└── report/
    └── validation_report.md
```

## Tools

SQL (SQLite: CTEs, anti-joins, aggregate reconciliation, `GLOB` pattern checks), Python, DBeaver.
