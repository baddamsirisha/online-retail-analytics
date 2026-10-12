-- 04_countries.sql : revenue by country with share of total
WITH c AS (
  SELECT country, SUM(revenue) AS revenue, COUNT(DISTINCT customer_id) AS customers
  FROM sales GROUP BY country
)
SELECT country,
       ROUND(revenue, 0)                                   AS revenue_gbp,
       customers,
       ROUND(100.0 * revenue / (SELECT SUM(revenue) FROM c), 2) AS share_pct
FROM c
ORDER BY revenue DESC;
