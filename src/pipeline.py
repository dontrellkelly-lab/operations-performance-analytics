"""Validate a daily batch and build reproducible SQLite management reports."""
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import time
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["location_id", "business_date", "orders", "gross_cents", "refund_cents",
          "labor_minutes", "completed_jobs", "on_time_jobs"]


def read_csv(path, fields):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != fields:
            raise ValueError(f"Unexpected schema: {path.name}; expected {fields}")
        result = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in result):
            raise ValueError(f"Malformed CSV row: {path.name}")
        return result


def iso_date(value):
    try:
        return date.fromisoformat(value).isoformat() == value
    except (ValueError, TypeError):
        return False


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate(row, locations, expected):
    errors = []
    if row["location_id"] not in locations:
        errors.append("UNKNOWN_LOCATION")
    if not iso_date(row["business_date"]):
        errors.append("INVALID_DATE")
    if (row["location_id"], row["business_date"]) not in expected:
        errors.append("UNEXPECTED_LOCATION_DATE")
    parsed = dict(row)
    for field in FIELDS[2:]:
        value = row[field]
        if not re.fullmatch(r"[0-9]+", value or ""):
            errors.append(f"INVALID_{field.upper()}")
        else:
            parsed[field] = int(value)
            if parsed[field] > 2**63 - 1:
                errors.append(f"OVERFLOW_{field.upper()}")
    if errors:
        return parsed, errors
    if parsed["refund_cents"] > parsed["gross_cents"]:
        errors.append("REFUND_EXCEEDS_GROSS")
    if parsed["completed_jobs"] > parsed["orders"]:
        errors.append("COMPLETED_EXCEEDS_ORDERS")
    if parsed["on_time_jobs"] > parsed["completed_jobs"]:
        errors.append("ON_TIME_EXCEEDS_COMPLETED")
    return parsed, errors


def run(input_dir, output_dir):
    started = time.perf_counter()
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    locations = read_csv(input_dir / "locations.csv", ["location_id", "region"])
    expected_rows = read_csv(input_dir / "expected_days.csv", ["location_id", "business_date"])
    rows = read_csv(input_dir / "daily_operations.csv", FIELDS)
    ids = {r["location_id"] for r in locations}
    expected = {(r["location_id"], r["business_date"]) for r in expected_rows}
    if not locations or len(ids) != len(locations) or any(not r["location_id"] or not r["region"] for r in locations):
        raise ValueError("Locations must be nonempty, unique, and complete")
    if not expected or len(expected) != len(expected_rows):
        raise ValueError("Expected calendar must be nonempty and unique")
    if any(site not in ids or not iso_date(day) for site, day in expected):
        raise ValueError("Invalid expected calendar")
    if {site for site, _ in expected} != ids:
        raise ValueError("Every location needs an explicit expected calendar")

    # Reject ALL rows for duplicated business keys. No ambiguous 'first row wins'.
    counts = Counter((r["location_id"], r["business_date"]) for r in rows)
    accepted, rejected = [], []
    rules = Counter()
    for row_number, row in enumerate(rows, start=2):
        parsed, errors = validate(row, ids, expected)
        if counts[(row["location_id"], row["business_date"])] > 1:
            errors.append("DUPLICATE_KEY")
        if errors:
            rules.update(errors)
            rejected.append({"source_row": row_number, "rules": "|".join(errors), **row})
        else:
            accepted.append(parsed)

    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / "sql/schema.sql").read_text())
    db.executemany("INSERT INTO locations VALUES (?, ?)", [(r["location_id"], r["region"]) for r in locations])
    db.executemany("INSERT INTO expected_days VALUES (?, ?)", sorted(expected))
    db.executemany("INSERT INTO daily_operations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   [tuple(r[f] for f in FIELDS) for r in accepted])
    db.commit()
    outputs = {}
    headers = {}
    for report in ("location_scorecard", "region_summary"):
        cursor = db.execute((ROOT / f"sql/{report}.sql").read_text())
        headers[report] = [d[0] for d in cursor.description]
        outputs[report] = [dict(r) for r in cursor]
    valid_keys = {(r["location_id"], r["business_date"]) for r in accepted}
    missing = [{"location_id": s, "business_date": d,
                "reason": "REJECTED_SOURCE" if (s, d) in counts else "NO_SOURCE_ROW"}
               for s, d in sorted(expected - valid_keys)]
    start_date, end_date = db.execute("SELECT MIN(business_date), MAX(business_date) FROM expected_days").fetchone()
    statuses = Counter(r["review_status"] for r in outputs["location_scorecard"])
    summary = {
        "data_type": "synthetic demonstration", "source_rows": len(rows),
        "accepted_rows": len(accepted), "quarantined_rows": len(rejected),
        "expected_location_days": len(expected), "unavailable_location_days": len(missing),
        "missing_day_reasons": dict(Counter(r["reason"] for r in missing)),
        "locations": len(locations), "calendar_start": start_date, "calendar_end": end_date,
        "rule_hits": dict(sorted(rules.items())), "location_review_status": dict(statuses),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(input_dir.glob("*.csv"))},
    }
    assert len(rows) == len(accepted) + len(rejected)
    assert len(expected) == len(accepted) + len(missing)
    output_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output_dir / "operations.sqlite") as saved:
        db.backup(saved)
    db.close()
    for report, result in outputs.items():
        write_csv(output_dir / f"{report}.csv", headers[report], result)
    write_csv(output_dir / "quarantine.csv", ["source_row", "rules"] + FIELDS, rejected)
    write_csv(output_dir / "missing_days.csv", ["location_id", "business_date", "reason"], missing)
    summary["runtime_seconds"] = round(time.perf_counter() - started, 3)
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = ["# Operations review — synthetic demonstration", "",
             f"Input period: {start_date} through {end_date}. Location/region metrics use the latest 28 calendar dates, or the available calendar if shorter.", "",
             "## Reporting reliability", "",
             f"- {len(locations):,} locations; {len(expected):,} expected location-days.",
             f"- {len(rows):,} source rows = {len(accepted):,} accepted + {len(rejected):,} quarantined.",
             f"- {len(missing):,} expected location-days lack a valid report; missing values are not treated as zero business activity.",
             "- Duplicate keys are fully quarantined pending a source correction; this intentionally favors reliability over apparent completeness.", "",
             "## Latest-window decisions", "",
             f"- Data follow-up first: {statuses['CHECK_DATA']} locations have less than 95% valid reporting coverage.",
             f"- Service follow-up: {statuses['REVIEW_SERVICE']} locations have at least 95% coverage but an on-time rate below 90%.",
             "- These are illustrative review thresholds, not validated business targets.", "",
             "| Location needing service review | Region | Valid / expected days | On-time rate |", "|---|---|---:|---:|"]
    for r in outputs["location_scorecard"]:
        if r["review_status"] == "REVIEW_SERVICE":
            lines.append(f"| {r['location_id']} | {r['region']} | {r['valid_days']} / {r['expected_days']} | {r['on_time_rate']:.1%} |")
    lines += ["", "## Recommended next actions", "",
              "1. Ask data owners to correct rejected submissions and resend missing reports. Rerun the complete batch after correction.",
              "2. For service flags, inspect daily workload, staffing and job complexity before proposing an intervention. The report does not establish a cause.",
              "3. Pilot any operational change and compare service outcomes with an appropriate baseline or control; no savings or service gains have been measured here.",
              "", "## Limits", "",
              "Revenue is gross less refunds, not profit. Metrics describe valid observed days and can remain biased by missingness even above the 95% threshold. Regions include incomplete locations and must be read with coverage. This batch prototype is not a production deployment or a benchmark of enterprise scalability.", ""]
    (output_dir / "executive_brief.md").write_text("\n".join(lines))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), indent=2))
