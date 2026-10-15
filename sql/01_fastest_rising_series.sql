-- Which detailed food series rose the most over the last 12 months?
-- CTE + window function (LAG over 12 months) + join to the labels
WITH yoy AS (
    SELECT series, month, value,
           100 * (value / LAG(value, 12) OVER (PARTITION BY series ORDER BY month) - 1) AS change_12m
    FROM fact_cpi
)
SELECT y.series, s.series_fr, ROUND(y.change_12m, 1) AS change_12m_pct
FROM yoy y
JOIN dim_series s USING (series)
WHERE y.month = (SELECT MAX(month) FROM fact_cpi)
  AND y.change_12m IS NOT NULL
  AND s.depth >= 4
ORDER BY change_12m_pct DESC
LIMIT 10;
