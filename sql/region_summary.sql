-- Same 28-day window as the location scorecard.
WITH bounds AS (
    SELECT MAX(business_date) AS end_date, DATE(MAX(business_date), '-27 days') AS start_date
    FROM expected_days
)
SELECT l.region, COUNT(*) AS expected_days, COUNT(d.business_date) AS valid_days,
       ROUND(100.0 * COUNT(d.business_date) / COUNT(*), 2) AS completeness_pct,
       SUM(d.gross_cents - d.refund_cents) / 100.0 AS net_revenue,
       1.0 * SUM(d.on_time_jobs) / NULLIF(SUM(d.completed_jobs), 0) AS on_time_rate,
       60.0 * SUM(d.orders) / NULLIF(SUM(d.labor_minutes), 0) AS orders_per_labor_hour
FROM expected_days e
JOIN locations l ON l.location_id = e.location_id
CROSS JOIN bounds b
LEFT JOIN daily_operations d ON d.location_id = e.location_id AND d.business_date = e.business_date
WHERE e.business_date BETWEEN b.start_date AND b.end_date
GROUP BY l.region
ORDER BY l.region;
