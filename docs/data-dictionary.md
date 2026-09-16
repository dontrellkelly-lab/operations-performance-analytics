# Data definitions and assumptions

All inputs are generated locally and are fictional. No external dataset is redistributed. Default seed: 42. Default calendar: January 1–June 29, 2025. Every generated location is expected to report every generated date; a real deployment would need an approved operating/reporting calendar.

## Inputs

| File / field | Grain or meaning | Validation |
|---|---|---|
| `locations.csv` | One row per location | Nonempty table; unique, nonblank location ID; nonblank region |
| `location_id` | Stable fictional location ID | Referenced by the calendar and facts |
| `region` | Fictional reporting region | Required |
| `expected_days.csv` | One row per location/date that should report | Unique, valid ISO date, known location; each location has a calendar |
| `daily_operations.csv` | One submitted summary per location/date, before validation | Exact expected column schema; duplicated keys fully quarantined |
| `business_date` | Local reporting date, `YYYY-MM-DD` | Valid ISO date; present in expected calendar |
| `orders` | Orders received on that date | Nonnegative integer |
| `gross_cents` | Gross value in fictional USD cents | Nonnegative integer |
| `refund_cents` | Same-date gross amount reversed, in cents | Nonnegative and no greater than gross |
| `labor_minutes` | Total staffed minutes for that location/date | Nonnegative integer; zero permitted |
| `completed_jobs` | Same-date orders completed | Nonnegative and no greater than orders |
| `on_time_jobs` | Completed jobs that met the fictional service target | Nonnegative and no greater than completed |

Integer values must fit SQLite's signed 64-bit range. The demo generator stays far below aggregate overflow limits. Numeric whitespace, fractions, negative values, and blanks are rejected rather than silently converted. Every malformed numeric row retains its original submitted values in quarantine.

These simplified definitions matter: real refunds may relate to an earlier date and real completions may exceed today's arrivals because of backlog. Such businesses need transaction/job-level data and different rules. Do not apply these constraints unchanged to those settings. The first prototype does not model tax, costs, opening/closing hours, customer counts, or profit.

## Output metrics

| Metric | Formula / meaning |
|---|---|
| Latest window | Latest expected business date and preceding 27 calendar dates; use only explicitly expected days in that interval |
| Expected days | Number of expected location/date keys in the reporting window |
| Valid days | Number of accepted location/date keys in the window |
| Completeness | 100 × valid days / expected days |
| Net revenue | Sum(gross cents − refund cents) / 100; valid days only |
| On-time rate | Sum(on-time jobs) / sum(completed jobs); null when no completed jobs |
| Orders per labor hour | 60 × sum(orders) / sum(labor minutes); null when no labor minutes |
| Refund rate | Sum(refund cents) / sum(gross cents); null when gross is zero |
| `CHECK_DATA` | Coverage below 95%; service review is deferred regardless of the observed rate |
| `NO_SERVICE_VOLUME` | Sufficient coverage but no completed jobs in the window |
| `REVIEW_SERVICE` | At least 95% coverage and on-time rate below 90% |
| `MONITOR` | Remaining locations; not a guarantee of good performance |

Regions aggregate raw accepted counts and amounts, not averages of location rates. Regional metrics include incomplete locations; always inspect coverage. The pipeline has no minimum service-volume reliability test yet. Add one with business input before ranking small-volume locations.

## Quality evidence

`quarantine.csv` records the CSV row number (header is row 1), all applicable rule codes, and the raw fields. Rule-hit counts can exceed the number of quarantined rows because one row can violate multiple rules.

`missing_days.csv` covers expected days across the entire input calendar, while location and region scorecards cover only the latest window. `REJECTED_SOURCE` means submissions exist for that exact key but none were accepted. `NO_SOURCE_ROW` means no submission has that key; this can include a record whose location ID was corrupted, not just a physically absent file.

Unknown locations fail both the location rule and expected-calendar rule. Multiple unknown IDs on the same date can also collide as duplicate keys. The generator's defects are intentional, and the system records observable failures without trying to reconstruct what a corrupted key should have been.

Row reconciliation: source rows = accepted rows + quarantined rows. Calendar reconciliation: expected location-days = accepted unique keys + unavailable location-days. These two checks use different denominators and are both asserted in code.

## Data flow and operational boundaries

The generator writes three CSVs. The pipeline validates reference data, rejects invalid facts, creates an in-memory SQLite database with relational constraints, runs SQL, and exports reports plus a local database copy. Source hashes identify the input bytes used. The run summary records local elapsed processing time; no speed comparison or hardware-independent performance promise is intended.

Batch reruns replace named outputs; source corrections are supplied by editing/resending the complete input batch and rerunning. There is no incremental update history, approval queue, freshness timestamp, or delivery log. Publishing all outputs as an atomic versioned bundle is a future production requirement.
