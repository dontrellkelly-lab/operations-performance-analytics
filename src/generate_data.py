"""Deterministic, fictional daily operations data. No employer data is used."""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

FIELDS = ["location_id", "business_date", "orders", "gross_cents", "refund_cents",
          "labor_minutes", "completed_jobs", "on_time_jobs"]


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def generate(output, locations=250, days=180, seed=42):
    if locations < 1 or days < 1:
        raise ValueError("locations and days must be positive")
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    start = date(2025, 1, 1)
    sites = [{"location_id": f"L{i:04}", "region": ["Central", "East", "South", "West"][i % 4]}
             for i in range(1, locations + 1)]
    expected, rows = [], []
    for site in sites:
        baseline = rng.randint(40, 220)
        for day in range(days):
            current = start + timedelta(days=day)
            expected.append({"location_id": site["location_id"], "business_date": current.isoformat()})
            if rng.random() < 0.012:
                continue
            orders = max(1, round(baseline * (1.2 if current.weekday() >= 5 else 1) * rng.uniform(.8, 1.2)))
            gross = orders * rng.randint(1800, 4500)
            completed = max(1, int(orders * rng.uniform(.85, 1)))
            row = dict(zip(FIELDS, [site["location_id"], current.isoformat(), orders, gross,
                                   round(gross * rng.uniform(.005, .05)), orders * rng.randint(3, 7),
                                   completed, round(completed * rng.uniform(.85, .99))]))
            if site["location_id"] == "L0017" and day >= days - 28:
                row["on_time_jobs"] = round(completed * .70)
            issue = rng.random()
            if issue < .003:
                row["gross_cents"] = -100
            elif issue < .006:
                row["refund_cents"] = gross + 1
            elif issue < .009:
                row["on_time_jobs"] = completed + 1
            elif issue < .012:
                row["labor_minutes"] = ""
            elif issue < .015:
                row["location_id"] = "UNKNOWN"
            rows.append(row)
            if rng.random() < .007:
                rows.append(row.copy())
    write_csv(output / "locations.csv", ["location_id", "region"], sites)
    write_csv(output / "expected_days.csv", ["location_id", "business_date"], expected)
    write_csv(output / "daily_operations.csv", FIELDS, rows)
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--locations", type=int, default=250)
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(f"Generated {generate(args.output, args.locations, args.days, args.seed):,} source rows.")
