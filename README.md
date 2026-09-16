# Multi-Location Operations Performance

**A reproducible reporting prototype for a fictional business with 250 locations.**

An operations leader needs to know which locations require attention. That decision is unreliable when daily submissions are missing, duplicated, or internally inconsistent. This project validates the reports first, then calculates comparable-window metrics and separates data follow-up from service follow-up.

**Status:** Working analytical prototype v0.1. AI-assisted initial scaffold; owner review and an interactive dashboard are planned. No production deployment or realized business impact is claimed.

## Read the result first

[Executive brief](outputs/executive_brief.md) · [Location scorecard](outputs/location_scorecard.csv) · [Regional summary](outputs/region_summary.csv)

The included seed-42 demonstration covers January 1–June 29, 2025:

| Measure | Result |
|---|---:|
| Locations | 250 |
| Expected location-days | 45,000 |
| Source rows | 44,772 |
| Accepted rows | 43,409 |
| Quarantined source rows | 1,363 |
| Expected days without a valid report | 1,591 |
| Locations needing data follow-up in the last 28 days | 69 |
| Locations needing service review with sufficient coverage | 1 |

The flagged service location is L0017, where the generator deliberately introduces lower on-time performance. This demonstrates detection of a known fictional scenario; it is not an independent business discovery. Missing-day counts and rejected-row counts measure different things, and rule-hit counts can overlap.

## Run it

Python 3.10 or later with the standard library is sufficient; no package installation, API key, cloud account, or database server is required. Tested here on Python 3.12.14.

From this project's folder, execute these commands in sequence:

```bash
python3 src/generate_data.py
python3 src/pipeline.py
python3 -m unittest discover -s tests -v
```

On Windows, use `python` instead of `python3` if that is your installed command. Generation replaces the three synthetic input CSVs; the pipeline replaces its named output files. Use a dedicated input/output folder and do not put employer data into this public demonstration.

For a separate simulation:

```bash
python3 src/generate_data.py --locations 500 --days 365 --seed 7 --output alternate-data
python3 src/pipeline.py --input alternate-data --output alternate-outputs
```

The alternate size is a supported parameter example, not a measured benchmark.

## What is included

| Path | Purpose |
|---|---|
| `src/generate_data.py` | Reproducible synthetic inputs and deliberately imperfect reports |
| `src/pipeline.py` | Schema checks, quarantine, database load, report generation |
| `sql/schema.sql` | Keys, relationships, numeric constraints |
| `sql/location_scorecard.sql` | Last-28-calendar-day metrics and review flags |
| `sql/region_summary.sql` | Weighted regional metrics over the same window |
| `tests/test_pipeline.py` | Seven behavior tests for duplicates, rates, missing data, reruns, and validation |
| `docs/data-dictionary.md` | Dataset grain, definitions, rules, and assumptions |
| `docs/walkthrough.md` | Analysis exercises, interview preparation, next release |
| `outputs/run_summary.json` | Row reconciliation, rule counts, source hashes, elapsed time |
| `outputs/quarantine.csv` | Raw rejected records, source row, and failed rules |
| `outputs/missing_days.csv` | Expected location-days without valid records |

## Design decisions

- Each fact row represents one location on one business date. An explicit expected calendar allows closures and reporting expectations to be represented independently of delivered records.
- Money is stored in integer cents. SQL converts to dollars for display; net revenue is gross less refunds, not profit.
- All versions of a duplicated key are rejected. A source owner must resolve the ambiguity; input order does not decide the winning version.
- Rates use total numerators and denominators. Zero denominators yield null, not a fabricated 0%.
- Reporting below 95% coverage receives `CHECK_DATA`; otherwise on-time performance below 90% receives `REVIEW_SERVICE`. These are illustrative rules, not learned or approved targets.
- Reruns rebuild a database from the batch instead of appending duplicate records. The input hashes support tracing a report to specific files.

## Validation and limits

Seven automated tests passed in the initial run. They cover weighted rates with missing days, conflicting duplicate versions, invalid refunds and unknown locations, genuine zero activity, reproducible reruns, missing columns, and invalid dates/numbers.

The full demonstration run reconciled both raw rows and expected days. It is a modest batch prototype; it does not prove performance at national production scale. It loads inputs in memory. It has no scheduler, authentication, messaging integration, incremental merge, or atomic multi-file output publication. A dashboard, trends, comparable-period analysis, and more extensive operational controls are future work.

Review flags are investigation prompts. They do not establish root causes, quantify recovered revenue, or demonstrate service improvement. Missingness can bias even sufficiently complete reports; regional totals include valid observed days from incomplete locations.

## Contribution and next steps

The initial scaffold was AI-assisted. Before the first portfolio release, Dontrell should run and explain the workflow, review the rules, make a substantive change, document findings, and record a short walkthrough. See [walkthrough and release checklist](docs/walkthrough.md).
