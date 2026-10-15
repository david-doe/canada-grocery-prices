-- Which tariffed series contribute most to the 2025 household cost? (share of total US imports, D21, D26)
-- Window SUM for shares and a running cumulative share (Pareto view)
WITH x AS (
    SELECT series, us_imports_mcad, exposure_s, spending_musd_cad
    FROM fact_exposure WHERE event_id = 'CA2025'
)
SELECT series,
       ROUND(us_imports_mcad)                                                        AS us_imports_m_cad,
       ROUND(100 * exposure_s, 1)                                                    AS us_share_of_spending_pct,
       ROUND(100 * us_imports_mcad / SUM(us_imports_mcad) OVER (), 1)                AS share_of_cost_pct,
       ROUND(100 * SUM(us_imports_mcad) OVER (ORDER BY us_imports_mcad DESC
             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(us_imports_mcad) OVER (), 1) AS cumulative_pct
FROM x
ORDER BY us_imports_mcad DESC;
