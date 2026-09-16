-- Exactly 28 calendar dates through the latest expected date; missing days stay missing.
-- Ratios use summed numerators/denominators, not an average of daily percentages.
WITH bounds AS (
    SELECT MAX(business_date) AS end_date,
           DATE(MAX(business_date), '-27 days') AS start_date FROM expected_days
), measures AS (
    SELECT l.location_id, l.region, COUNT(*) AS expected_days,
           COUNT(d.business_date) AS valid_days,
           SUM(d.gross_cents - d.refund_cents) / 100.0 AS net_revenue,
           1.0 * SUM(d.on_time_jobs) / NULLIF(SUM(d.completed_jobs), 0) AS on_time_rate,
           60.0 * SUM(d.orders) / NULLIF(SUM(d.labor_minutes), 0) AS orders_per_labor_hour,
           1.0 * SUM(d.refund_cents) / NULLIF(SUM(d.gross_cents), 0) AS refund_rate
    FROM expected_days e
    JOIN locations l ON l.location_id = e.location_id
    CROSS JOIN bounds b
    LEFT JOIN daily_operations d ON d.location_id = e.location_id AND d.business_date = e.business_date
    WHERE e.business_date BETWEEN b.start_date AND b.end_date
    GROUP BY l.location_id, l.region
)
SELECT *, ROUND(100.0 * valid_days / expected_days, 2) AS completeness_pct,
       CASE WHEN 1.0 * valid_days / expected_days < 0.95 THEN 'CHECK_DATA'
            WHEN on_time_rate IS NULL THEN 'NO_SERVICE_VOLUME'
            WHEN on_time_rate < 0.90 THEN 'REVIEW_SERVICE'
            ELSE 'MONITOR' END AS review_status
FROM measures
ORDER BY CASE WHEN 1.0 * valid_days / expected_days < 0.95 THEN 0 ELSE 1 END,
         on_time_rate, location_id;
