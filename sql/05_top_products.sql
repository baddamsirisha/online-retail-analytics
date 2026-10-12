-- 05_top_products.sql : top 10 products by revenue
SELECT stock_code,
       MAX(description)           AS description,
       ROUND(SUM(revenue), 0)     AS revenue_gbp,
       SUM(quantity)              AS units,
       COUNT(DISTINCT invoice)    AS orders
FROM sales
GROUP BY stock_code
ORDER BY revenue_gbp DESC
LIMIT 10;
