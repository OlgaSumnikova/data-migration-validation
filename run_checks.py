"""
Run every SQL check in sql/ against the source and target databases
and write a Markdown report to report/validation_report.md.

Rule for every check: the query returns the PROBLEM rows.
0 rows = PASS, any rows = FAIL.

Exit code is 1 if any check fails, so the script can run in CI.
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SQL_DIR = ROOT / "sql"
DATA_DIR = ROOT / "data"
REPORT = ROOT / "report" / "validation_report.md"
SAMPLE_ROWS = 10


def parse_header(sql_text):
    meta = {"check": "", "severity": "", "why": ""}
    for line in sql_text.splitlines():
        line = line.strip()
        if not line.startswith("--"):
            continue
        body = line[2:].strip()
        for key in meta:
            if body.lower().startswith(key + ":"):
                meta[key] = body[len(key) + 1:].strip()
    return meta


def fmt(value):
    if value is None:
        return "NULL"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value).replace("|", "\\|")


def md_table(columns, rows):
    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    out += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join(out)


def main():
    if not (DATA_DIR / "legacy.db").exists() or not (DATA_DIR / "target.db").exists():
        import generate_data
        generate_data.main()

    con = sqlite3.connect(":memory:")
    con.execute(f"ATTACH DATABASE '{DATA_DIR / 'legacy.db'}' AS src")
    con.execute(f"ATTACH DATABASE '{DATA_DIR / 'target.db'}' AS tgt")

    results = []
    for path in sorted(SQL_DIR.glob("*.sql")):
        sql_text = path.read_text(encoding="utf-8")
        meta = parse_header(sql_text)
        cur = con.execute(sql_text)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        results.append({"file": path.name, **meta, "columns": columns, "rows": rows})

    failed = [r for r in results if r["rows"]]

    lines = [
        "# Data Migration Validation Report",
        "",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M}  ",
        f"Checks run: {len(results)} | Passed: {len(results) - len(failed)} | Failed: {len(failed)}",
        "",
        "## Summary",
        "",
        "| # | Check | Severity | Result | Problem rows |",
        "|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        status = "❌ FAIL" if r["rows"] else "✅ PASS"
        lines.append(f"| {i} | {r['check']} | {r['severity']} | {status} | {len(r['rows'])} |")

    lines += ["", "## Failed checks", ""]
    for r in failed:
        lines += [
            f"### {r['check']}",
            "",
            f"**Severity:** {r['severity']}  ",
            f"**Why it matters:** {r['why']}  ",
            f"**Query:** [`sql/{r['file']}`](../sql/{r['file']})  ",
            f"**Problem rows:** {len(r['rows'])}"
            + (f" (showing first {SAMPLE_ROWS})" if len(r["rows"]) > SAMPLE_ROWS else ""),
            "",
            md_table(r["columns"], r["rows"][:SAMPLE_ROWS]),
            "",
        ]

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    for i, r in enumerate(results, 1):
        status = "FAIL" if r["rows"] else "PASS"
        print(f"{i:>2}. [{status}] {r['check']} ({len(r['rows'])} rows)")
    print(f"\nReport written to {REPORT.relative_to(ROOT)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
