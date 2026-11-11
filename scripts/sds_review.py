"""SDS review check for the SDS library.

Reads sds-review.csv and reports which safety data sheets should be checked
with the supplier. Standard library only, no network access.

Rules (keep in step with REVIEW_* in index.html):
  * A sheet is DUE when its SDS date is 3 or more years old AND nobody has
    confirmed it with the supplier in the last 12 months.
  * A sheet is also DUE when the problem column is filled in (wrong version,
    label instead of SDS, ...) or its SDS date is missing.

Ontario does not make SDS expire: an older sheet is fine as long as it is still
the supplier's latest version. "Checking" means asking the supplier (or their
SDS portal) whether a newer version exists. If not, put today's date in
last_checked. If so, replace the PDF and update sds_date and last_checked.

Usage:
  python3 scripts/sds_review.py --check              validate the CSV, print a summary
  python3 scripts/sds_review.py --issue-body out.md  also write the reminder text;
                                                     prints the number of sheets due
"""
import argparse
import csv
import datetime as dt
import os
import re
import sys

REVIEW_AFTER_YEARS = 3
RECHECK_AFTER_MONTHS = 12

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "sds-review.csv")
SDS_DIR = os.path.join(ROOT, "sds")
COLUMNS = ["id", "product", "supplier", "sds_date", "last_checked", "problem", "notes"]
ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{0,99}$")
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def parse_date(value):
    return dt.date.fromisoformat(value) if value else None


def years_between(a, b):
    return (b - a).days / 365.25


def load(today):
    """Return (rows, errors). Every row gets parsed dates added."""
    errors = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            return [], [f"Header must be exactly: {','.join(COLUMNS)}"]
        rows = list(reader)

    seen = set()
    for n, r in enumerate(rows, start=2):
        rid = (r.get("id") or "").strip()
        if not ID_RE.match(rid):
            errors.append(f"line {n}: bad id {rid!r}")
            continue
        if rid in seen:
            errors.append(f"line {n}: duplicate id {rid}")
        seen.add(rid)
        if not os.path.isfile(os.path.join(SDS_DIR, rid + ".pdf")):
            errors.append(f"line {n}: no file sds/{rid}.pdf")
        for col in COLUMNS:
            val = r.get(col) or ""
            if val.startswith(FORMULA_START):
                errors.append(f"line {n}: {col} starts with {val[0]!r}; Excel would treat it as a formula")
        for col in ("sds_date", "last_checked"):
            try:
                d = parse_date((r.get(col) or "").strip())
            except ValueError:
                errors.append(f"line {n}: {col} must be YYYY-MM-DD, got {r.get(col)!r}")
                d = None
            if d and d > today:
                errors.append(f"line {n}: {col} {d} is in the future")
            r["_" + col] = d

    pdfs = {f[:-4] for f in os.listdir(SDS_DIR) if f.lower().endswith(".pdf")}
    for missing in sorted(pdfs - seen):
        errors.append(f"sds/{missing}.pdf has no row in sds-review.csv")
    return rows, errors


def reasons_due(r, today):
    out = []
    if (r.get("problem") or "").strip():
        out.append(r["problem"].strip())
    sds = r.get("_sds_date")
    checked = r.get("_last_checked")
    if not sds:
        out.append("SDS date unknown")
    elif years_between(sds, today) >= REVIEW_AFTER_YEARS:
        if not checked or (today - checked).days > RECHECK_AFTER_MONTHS * 30.44:
            out.append(f"SDS dated {sds.isoformat()}, not confirmed with supplier"
                       + (f" since {checked.isoformat()}" if checked else ""))
    return out


def issue_body(rows, today):
    due = [(r, reasons_due(r, today)) for r in rows]
    due = [(r, why) for r, why in due if why]
    by_supplier = {}
    for r, why in due:
        by_supplier.setdefault(r["supplier"] or "Unknown supplier", []).append((r, why))

    lines = [
        f"**{len(due)} of {len(rows)} safety data sheets need a check with the supplier** "
        f"(as of {today.isoformat()}).",
        "",
        "SDS don't expire in Ontario. For each sheet below, ask the supplier (or their SDS portal) "
        "whether a newer version exists:",
        "- **No newer version:** put today's date in `last_checked` in `sds-review.csv`.",
        "- **Newer version:** upload it over the old PDF in `sds/` (same file name), then update "
        "`sds_date` and `last_checked`.",
        "",
        "This issue updates itself each month and closes when nothing is due.",
        "",
    ]
    for supplier in sorted(by_supplier, key=lambda s: (-len(by_supplier[s]), s.lower())):
        items = sorted(by_supplier[supplier], key=lambda x: (x[0]["sds_date"] or "", x[0]["product"].lower()))
        lines.append(f"### {supplier} ({len(items)})")
        lines.append("| Product | SDS date | Why |")
        lines.append("|---|---|---|")
        for r, why in items:
            cell = "; ".join(why).replace("|", "/")
            lines.append(f"| {r['product'].replace('|', '/')} | {r['sds_date'] or '?'} | {cell} |")
        lines.append("")
    return "\n".join(lines), len(due)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--issue-body")
    ap.add_argument("--today", help="override today's date (testing)")
    args = ap.parse_args()
    today = parse_date(args.today) if args.today else dt.date.today()

    rows, errors = load(today)
    if errors:
        print("sds-review.csv has problems:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    body, n_due = issue_body(rows, today)
    if args.issue_body:
        with open(args.issue_body, "w", encoding="utf-8") as f:
            f.write(body)
        print(n_due)
    else:
        print(f"OK: {len(rows)} sheets, {n_due} due for a supplier check.")


if __name__ == "__main__":
    main()
