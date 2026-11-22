"""
Generate two SQLite databases:
  data/legacy.db  - the source system (old e-commerce shop)
  data/target.db  - the same data after migration to a new platform

The migration logic below intentionally contains bugs that are common in real
data migrations (lost batches, retries creating duplicates, type conversion
errors, missing value mappings, field truncation, date-format parsing errors).
The goal of the project is to FIND them with SQL validation checks.

The data is fully synthetic. Fixed seed -> the same output on every run.
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_CUSTOMERS = 500
N_ORDERS = 2000
DATA_DIR = Path(__file__).parent / "data"

FIRST_NAMES = [
    "Olena", "Andrii", "Maria", "Taras", "Iryna", "Dmytro", "Sofia", "Oleksandr",
    "Anna", "Maksym", "Kateryna", "Ivan", "Emma", "Lukas", "Chloé", "José", "Zoë", "Mateo",
]
LAST_NAMES = [
    "Shevchenko", "Kovalenko", "Bondarenko", "Tkachenko", "Kravchenko", "Melnyk",
    "Smith", "García", "Müller", "Novak", "Wiśniewska", "Oliynyk",
    "Petrenko-Kovalchuk", "Kovalchuk-Dombrovskyi", "Van der Westhuizen-Smit",
]
DOMAINS = ["gmail.com", "ukr.net", "outlook.com", "example.com"]
STATUSES = ["NEW", "PAID", "SHIPPED", "CANCELED", "REFUNDED"]
STATUS_WEIGHTS = [10, 30, 45, 10, 5]
CURRENCIES = ["UAH", "EUR", "USD"]
CURRENCY_WEIGHTS = [70, 20, 10]

# Correct mapping, as written in the migration spec
STATUS_MAPPING_SPEC = {
    "NEW": "new", "PAID": "paid", "SHIPPED": "shipped",
    "CANCELED": "cancelled", "REFUNDED": "refunded",
}

START_DATE = date(2021, 1, 1)
END_DATE = date(2026, 10, 31)


def random_date(rng, start, end):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def legacy_date(d):
    """Legacy system stores dates as text DD.MM.YYYY."""
    return d.strftime("%d.%m.%Y")


def random_phone(rng):
    digits = "".join(str(rng.randint(0, 9)) for _ in range(7))
    operator = rng.choice(["67", "50", "63", "93", "97", "66"])
    fmt = rng.choices(["e164", "spaced", "local", "none"], weights=[55, 25, 12, 8])[0]
    if fmt == "e164":
        return f"+380{operator}{digits}"
    if fmt == "spaced":
        return f"+38 0{operator} {digits[:3]} {digits[3:5]} {digits[5:]}"
    if fmt == "local":
        return f"(0{operator}) {digits[:3]}-{digits[3:5]}-{digits[5:]}"
    return None


def random_email(rng, customer_id):
    email = f"customer{customer_id}@{rng.choice(DOMAINS)}"
    # Legacy UI did not normalise input: mixed case and stray spaces
    if rng.random() < 0.2:
        email = email.capitalize()
    if rng.random() < 0.1:
        email = email.upper()
    if rng.random() < 0.1:
        email = f" {email} "
    return email


# ---------------------------------------------------------------------------
# Source (legacy) data
# ---------------------------------------------------------------------------
def build_legacy(rng):
    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        full_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        reg = random_date(rng, START_DATE, END_DATE - timedelta(days=30))
        customers.append({
            "customer_id": cid,
            "full_name": full_name,
            "email": random_email(rng, cid),
            "phone": random_phone(rng),
            "reg_date": reg,
        })

    orders = []
    for oid in range(1, N_ORDERS + 1):
        c = rng.choice(customers)
        orders.append({
            "order_id": oid,
            "customer_id": c["customer_id"],
            "amount_cents": rng.randint(199, 49_999),
            "currency": rng.choices(CURRENCIES, weights=CURRENCY_WEIGHTS)[0],
            "status": rng.choices(STATUSES, weights=STATUS_WEIGHTS)[0],
            "order_date": random_date(rng, c["reg_date"], END_DATE),
        })
    return customers, orders


def write_legacy(path, customers, orders):
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            full_name   TEXT NOT NULL,
            email       TEXT NOT NULL,
            phone       TEXT,
            created_at  TEXT NOT NULL          -- DD.MM.YYYY
        );
        CREATE TABLE orders (
            order_id     INTEGER PRIMARY KEY,
            customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
            amount_cents INTEGER NOT NULL,     -- money stored in minor units
            currency     TEXT NOT NULL,
            status       TEXT NOT NULL,        -- NEW / PAID / SHIPPED / CANCELED / REFUNDED
            created_at   TEXT NOT NULL         -- DD.MM.YYYY
        );
    """)
    con.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
        [(c["customer_id"], c["full_name"], c["email"], c["phone"], legacy_date(c["reg_date"]))
         for c in customers],
    )
    con.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
        [(o["order_id"], o["customer_id"], o["amount_cents"], o["currency"], o["status"],
          legacy_date(o["order_date"])) for o in orders],
    )
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# Migration with injected bugs
# ---------------------------------------------------------------------------
def buggy_parse_date(text, swap_day_month):
    """BUG: one migration batch parsed DD.MM.YYYY as MM.DD.YYYY when possible."""
    dd, mm, yyyy = text.split(".")
    if swap_day_month and int(dd) <= 12:
        dd, mm = mm, dd
    return f"{yyyy}-{mm}-{dd}"


def buggy_normalise_phone(phone):
    """BUG: only formats that start with '+' are handled; '(0xx) ...' becomes NULL."""
    if phone is None or not phone.startswith("+"):
        return None
    digits = "".join(ch for ch in phone if ch.isdigit())
    return f"+{digits}"


def migrate(rng, customers, orders):
    missing_customers = set(rng.sample(range(1, N_CUSTOMERS + 1), 3))
    duplicated_customers = set(rng.sample(
        [i for i in range(1, N_CUSTOMERS + 1) if i not in missing_customers], 4))
    date_bug_batch = range(301, 361)              # customers migrated in a faulty batch
    missing_orders = set(range(1501, 1513))       # a failed batch of 12 orders
    lost_cents_orders = set(rng.sample(
        [o["order_id"] for o in orders
         if o["amount_cents"] % 100 != 0 and o["order_id"] not in missing_orders], 30))

    target_customers, legacy_to_target = [], {}
    next_id = 1
    for c in customers:
        if c["customer_id"] in missing_customers:
            continue
        first, last = c["full_name"].split(" ", 1)
        row = {
            "legacy_id": c["customer_id"],
            "first_name": first,
            "last_name": last[:20],               # BUG: VARCHAR(20) silently truncates
            "email": c["email"].strip().lower(),  # correct normalisation
            "phone": buggy_normalise_phone(c["phone"]),
            "created_at": buggy_parse_date(legacy_date(c["reg_date"]),
                                           c["customer_id"] in date_bug_batch),
        }
        copies = 2 if c["customer_id"] in duplicated_customers else 1  # BUG: retry re-insert
        for _ in range(copies):
            target_customers.append({"id": next_id, **row})
            legacy_to_target.setdefault(c["customer_id"], next_id)
            next_id += 1

    target_orders, next_order_id = [], 1
    for o in orders:
        if o["order_id"] in missing_orders:
            continue
        if o["order_id"] in lost_cents_orders:
            total = float(o["amount_cents"] // 100)   # BUG: integer division drops cents
        else:
            total = round(o["amount_cents"] / 100, 2)
        # BUG: REFUNDED is missing from the code's mapping table, falls back to 'paid'
        code_mapping = {k: v for k, v in STATUS_MAPPING_SPEC.items() if k != "REFUNDED"}
        target_orders.append({
            "id": next_order_id,
            "legacy_id": o["order_id"],
            "customer_id": legacy_to_target.get(o["customer_id"]),  # NULL if customer lost
            "total": total,
            "currency": o["currency"],
            "status": code_mapping.get(o["status"], "paid"),
            "created_at": o["order_date"].isoformat(),
        })
        next_order_id += 1
    return target_customers, target_orders


def write_target(path, customers, orders):
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE customers (
            id          INTEGER PRIMARY KEY,
            legacy_id   INTEGER NOT NULL,      -- no UNIQUE constraint (part of the problem)
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            email       TEXT NOT NULL,
            phone       TEXT,                  -- E.164, e.g. +380671234567
            created_at  TEXT NOT NULL          -- ISO YYYY-MM-DD
        );
        CREATE TABLE orders (
            id          INTEGER PRIMARY KEY,
            legacy_id   INTEGER NOT NULL,
            customer_id INTEGER,               -- FK to customers.id, not enforced
            total       REAL NOT NULL,         -- major units, 2 decimals
            currency    TEXT NOT NULL,
            status      TEXT NOT NULL,         -- lower-case statuses
            created_at  TEXT NOT NULL          -- ISO YYYY-MM-DD
        );
    """)
    cols_c = ["id", "legacy_id", "first_name", "last_name", "email", "phone", "created_at"]
    cols_o = ["id", "legacy_id", "customer_id", "total", "currency", "status", "created_at"]
    con.executemany(f"INSERT INTO customers VALUES ({','.join('?' * len(cols_c))})",
                    [tuple(c[k] for k in cols_c) for c in customers])
    con.executemany(f"INSERT INTO orders VALUES ({','.join('?' * len(cols_o))})",
                    [tuple(o[k] for k in cols_o) for o in orders])
    con.commit()
    con.close()


def main():
    rng = random.Random(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    customers, orders = build_legacy(rng)
    write_legacy(DATA_DIR / "legacy.db", customers, orders)
    t_customers, t_orders = migrate(rng, customers, orders)
    write_target(DATA_DIR / "target.db", t_customers, t_orders)
    print(f"legacy.db: {len(customers)} customers, {len(orders)} orders")
    print(f"target.db: {len(t_customers)} customers, {len(t_orders)} orders")


if __name__ == "__main__":
    main()
