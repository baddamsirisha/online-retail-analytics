-- 02_kpis.sql : headline KPIs per year
SELECT substr(month,1,4)                         AS year,
       ROUND(SUM(revenue), 0)                    AS revenue_gbp,
       COUNT(DISTINCT invoice)                   AS orders,
       COUNT(DISTINCT customer_id)               AS customers,
       ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2) AS avg_order_value_gbp
FROM sales
GROUP BY year
ORDER BY year;
