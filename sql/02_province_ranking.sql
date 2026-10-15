-- How do provinces rank on grocery inflation in the latest month, and how far from Canada?
-- Window ranking + self-join on the national value
WITH latest AS (
    SELECT * FROM fact_province WHERE month = (SELECT MAX(month) FROM fact_province)
)
SELECT p.geo,
       ROUND(p.yoy, 1)                         AS change_12m_pct,
       ROUND(p.yoy - c.yoy, 1)                 AS gap_vs_canada_pts,
       RANK() OVER (ORDER BY p.yoy DESC)       AS rank_highest
FROM latest p
CROSS JOIN (SELECT yoy FROM latest WHERE geo = 'Canada') c
WHERE p.geo <> 'Canada'
ORDER BY rank_highest;
