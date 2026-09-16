# Review and first public release

## Start with the business question

Which locations need management attention, and where should unreliable reporting be corrected before drawing conclusions?

The included executive brief gives the result. Trace one location from raw records through validation to the SQL scorecard. L0017 is the intentionally degraded service case. Inspect a `CHECK_DATA` location as well and explain why the system prioritizes data follow-up.

## Suggested three-minute walkthrough

1. **First 30 seconds:** Explain the fictional company, the reporting problem, and the decision the system supports.
2. **Next 45 seconds:** Show the executive brief and contrast a service-review location with a data-follow-up location. Explain coverage and the metric denominator.
3. **Next 60 seconds:** Show the SQL and one quarantined record. Explain why duplicates are rejected and why rates use summed counts.
4. **Final 45 seconds:** Give the next action, the main limitation, and the change you personally made and validated.

Record this after you have run and reviewed the project. No recording is included yet.

## Exercises that turn the scaffold into your work

- Recalculate one location's on-time rate manually or in a spreadsheet and compare it to the SQL result.
- Choose a reporting-completeness threshold and explain the business trade-off before changing it. The first version stores its thresholds directly in SQL; moving them to configuration is a useful extension.
- Find a duplicate key in quarantine. Decide what evidence would be required before choosing a correct version; do not simply delete whichever row is inconvenient.
- Explain the consequence of adding a closed date to the expected calendar. Then change the calendar and predict the output before rerunning.
- Add a prior-period comparison. Define both periods and minimum comparable coverage before displaying percentage changes.
- Write two recommendations in your own words: one for the data owner and one for an operations manager. State what would need to be measured to establish improvement.

## Dashboard brief for the next release

Audience: an operations director and regional managers.

Top view: reporting window, net revenue, on-time rate, orders per labor hour, and coverage. Always display the coverage context alongside business totals. Add region and location filters.

Below: a location table with review status; a regional comparison; daily/weekly trends; an exception detail view showing failed rules and missing days. The v0.1 CSV scorecards are summary extracts. For trends or recomputable filtering, export the underlying accepted daily facts and expected calendar or connect through a suitable SQLite connector; do not sum or average precomputed rates.

An executive should be able to answer “What needs my attention?” quickly and then inspect the evidence. Capture three screenshots and put the overview near the top of the repository README.

## Questions you should be able to answer

- What is the grain of each table, and which keys prevent duplicated metrics?
- Why is a weighted rate different from an average percentage?
- Why are missing days not imputed as zero revenue?
- What makes 95% coverage sufficient here, and what does it fail to protect against?
- Why could a region look healthier than one of its locations?
- What would change if refunds could exceed the same day's sales?
- Can the data establish why service performance deteriorated?
- What must change for scheduled, secure production use?
- What did you personally implement or change, and what assistance did you use?

## Contribution log

| Stage | Contributor / status | Evidence |
|---|---|---|
| Initial prototype | Prepared with AI assistance, September 15, 2026 | Generator, Python pipeline, SQL, tests, documentation, sample run |
| Business-rule review | Dontrell — pending | Add decisions and rationale after review |
| Substantive modification | Dontrell — pending | Add commit reference and validation result |
| Dashboard and case study | Pending | Add files/screenshots and conclusions |
| Interview walkthrough | Pending | Add recording link when available |

## Release checklist

- [ ] Run locally and explain the three SQL files.
- [ ] Verify one result independently and document it.
- [ ] Make and validate one meaningful business or analytical change.
- [ ] Add a dashboard or clear visual overview with coverage context.
- [ ] Add your recommendations and a short walkthrough.
- [ ] Keep synthetic-data and AI-assistance provenance accurate.
- [ ] Confirm all profile and education wording is accurate.
- [ ] Publish actual code/results and link them from the profile.

The release gate is your ability to explain and maintain the project, not merely the presence of files in a repository.
