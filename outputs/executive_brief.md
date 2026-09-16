# Operations review — synthetic demonstration

Input period: 2025-01-01 through 2025-06-29. Location/region metrics use the latest 28 calendar dates, or the available calendar if shorter.

## Reporting reliability

- 250 locations; 45,000 expected location-days.
- 44,772 source rows = 43,409 accepted + 1,363 quarantined.
- 1,591 expected location-days lack a valid report; missing values are not treated as zero business activity.
- Duplicate keys are fully quarantined pending a source correction; this intentionally favors reliability over apparent completeness.

## Latest-window decisions

- Data follow-up first: 69 locations have less than 95% valid reporting coverage.
- Service follow-up: 1 locations have at least 95% coverage but an on-time rate below 90%.
- These are illustrative review thresholds, not validated business targets.

| Location needing service review | Region | Valid / expected days | On-time rate |
|---|---|---:|---:|
| L0017 | East | 27 / 28 | 69.9% |

## Recommended next actions

1. Ask data owners to correct rejected submissions and resend missing reports. Rerun the complete batch after correction.
2. For service flags, inspect daily workload, staffing and job complexity before proposing an intervention. The report does not establish a cause.
3. Pilot any operational change and compare service outcomes with an appropriate baseline or control; no savings or service gains have been measured here.

## Limits

Revenue is gross less refunds, not profit. Metrics describe valid observed days and can remain biased by missingness even above the 95% threshold. Regions include incomplete locations and must be read with coverage. This batch prototype is not a production deployment or a benchmark of enterprise scalability.
