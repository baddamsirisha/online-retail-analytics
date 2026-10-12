-- 03_monthly_revenue.sql : revenue and orders per month
SELECT month,
       ROUND(SUM(revenue), 0)       AS revenue_gbp,
       COUNT(DISTINCT invoice)      AS orders,
       COUNT(DISTINCT customer_id)  AS active_customers
FROM sales
WHERE month < '2011-12'            -- Dec 2011 is only partially covered
GROUP BY month
ORDER BY month;
