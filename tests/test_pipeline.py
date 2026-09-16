"""Behavior tests for misleading metrics, ambiguous duplicates, and missing data."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from generate_data import write_csv
from pipeline import FIELDS, run


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.out = self.root / "outputs"
        write_csv(self.data / "locations.csv", ["location_id", "region"],
                  [{"location_id": "L1", "region": "East"}])
        write_csv(self.data / "expected_days.csv", ["location_id", "business_date"],
                  [{"location_id": "L1", "business_date": f"2025-01-{i:02}"} for i in range(1, 4)])

    def tearDown(self):
        self.temp.cleanup()

    def row(self, day="2025-01-01", **changes):
        result = dict(zip(FIELDS, ["L1", day, 100, 100000, 1000, 600, 100, 90]))
        result.update(changes)
        return result

    def execute(self, rows):
        write_csv(self.data / "daily_operations.csv", FIELDS, rows)
        return run(self.data, self.out)

    def output(self, name):
        with (self.out / name).open() as f:
            return list(csv.DictReader(f))

    def test_weighted_rates_and_missing_day(self):
        s = self.execute([self.row(), self.row("2025-01-02", orders=1, completed_jobs=1, on_time_jobs=0)])
        r = self.output("location_scorecard.csv")[0]
        self.assertAlmostEqual(float(r["on_time_rate"]), 90 / 101)
        self.assertEqual(s["unavailable_location_days"], 1)
        self.assertEqual(r["review_status"], "CHECK_DATA")

    def test_all_duplicate_versions_quarantined(self):
        s = self.execute([self.row(), self.row(gross_cents=200000)])
        self.assertEqual(s["accepted_rows"], 0)
        self.assertEqual(s["quarantined_rows"], 2)
        self.assertEqual(s["rule_hits"]["DUPLICATE_KEY"], 2)
        self.assertEqual(s["missing_day_reasons"]["REJECTED_SOURCE"], 1)

    def test_impossible_refund_and_unknown_location(self):
        s = self.execute([self.row(refund_cents=100001), self.row("2025-01-02", location_id="BOGUS")])
        self.assertEqual(s["accepted_rows"], 0)
        self.assertEqual(s["rule_hits"]["REFUND_EXCEEDS_GROSS"], 1)
        self.assertEqual(s["rule_hits"]["UNKNOWN_LOCATION"], 1)

    def test_zero_activity_is_valid_and_rates_are_null(self):
        self.execute([self.row(f"2025-01-{i:02}", orders=0, gross_cents=0, refund_cents=0,
                               labor_minutes=0, completed_jobs=0, on_time_jobs=0) for i in range(1, 4)])
        r = self.output("location_scorecard.csv")[0]
        self.assertEqual(r["completeness_pct"], "100.0")
        self.assertEqual(r["on_time_rate"], "")
        self.assertEqual(r["review_status"], "NO_SERVICE_VOLUME")

    def test_rerun_does_not_duplicate_and_hashes_stable(self):
        first = self.execute([self.row()])
        original = (self.out / "location_scorecard.csv").read_bytes()
        second = run(self.data, self.out)
        self.assertEqual(first["source_sha256"], second["source_sha256"])
        self.assertEqual(first["accepted_rows"], second["accepted_rows"])
        self.assertEqual(original, (self.out / "location_scorecard.csv").read_bytes())

    def test_missing_schema_column_fails(self):
        write_csv(self.data / "daily_operations.csv", FIELDS[:-1], [])
        with self.assertRaises(ValueError):
            run(self.data, self.out)

    def test_bad_date_and_noninteger_fail(self):
        s = self.execute([self.row("2025-02-30"), self.row("2025-01-02", orders="1.5")])
        self.assertEqual(s["quarantined_rows"], 2)
        self.assertEqual(s["rule_hits"]["INVALID_DATE"], 1)
        self.assertEqual(s["rule_hits"]["INVALID_ORDERS"], 1)


if __name__ == "__main__":
    unittest.main()
