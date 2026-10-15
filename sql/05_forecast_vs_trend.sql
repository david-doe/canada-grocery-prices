-- Where does the 12-month forecast depart most from the last 12 months? (expected acceleration or slowdown)
-- Two CTEs: past change with LAG, forecast change at horizon 12, then the difference
WITH past AS (
    SELECT series, value AS last_value,
           100 * (value / LAG(value, 12) OVER (PARTITION BY series ORDER BY month) - 1) AS past_12m
    FROM fact_cpi
    QUALIFY month = MAX(month) OVER ()
),
ahead AS (
    SELECT series, forecast FROM fact_forecast WHERE h = 12
)
SELECT p.series,
       ROUND(p.past_12m, 1)                                         AS past_12m_pct,
       ROUND(100 * (a.forecast / p.last_value - 1), 1)              AS next_12m_pct,
       ROUND(100 * (a.forecast / p.last_value - 1) - p.past_12m, 1) AS change_in_pace_pts
FROM past p JOIN ahead a USING (series)
WHERE p.past_12m IS NOT NULL
ORDER BY ABS(change_in_pace_pts) DESC
LIMIT 10;
