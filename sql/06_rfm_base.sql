-- 06_rfm_base.sql : Recency / Frequency / Monetary per customer
-- Reference date = day after the last transaction in the data.
WITH ref AS (SELECT date(MAX(invoice_date), '+1 day') AS d FROM sales)
SELECT customer_id,
       CAST(julianday((SELECT d FROM ref)) - julianday(MAX(date(invoice_date))) AS INTEGER) AS recency_days,
       COUNT(DISTINCT invoice)   AS frequency,
       ROUND(SUM(revenue), 2)    AS monetary_gbp
FROM sales
WHERE customer_id IS NOT NULL
GROUP BY customer_id;
