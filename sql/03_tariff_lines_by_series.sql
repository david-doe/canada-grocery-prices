-- For each tariff episode, how many tariff lines fall in each CPI series, and how many are directly taxed?
-- Join of the line table with the many-to-many mapping, conditional aggregation
SELECT m.event_id,
       m.cpi_product,
       SUM(CAST(l.n_lines AS INTEGER))                                         AS tariff_lines,
       SUM(CASE WHEN m.exposure = 'direct' THEN CAST(l.n_lines AS INTEGER) ELSE 0 END) AS direct_lines,
       STRING_AGG(DISTINCT l.access, '')                                         AS access_types
FROM map_tariff_cpi m
JOIN dim_tariff_line l ON l.event_id = m.event_id AND l.hs6 = m.hs6
GROUP BY m.event_id, m.cpi_product
ORDER BY m.event_id, tariff_lines DESC;
