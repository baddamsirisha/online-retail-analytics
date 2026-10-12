-- 08_cancellations.sql : share of invoices that were cancelled, per country (raw data)
SELECT Country AS country,
       COUNT(DISTINCT Invoice) AS invoices,
       COUNT(DISTINCT CASE WHEN Invoice LIKE 'C%' THEN Invoice END) AS cancelled,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN Invoice LIKE 'C%' THEN Invoice END) / COUNT(DISTINCT Invoice), 1) AS cancel_rate_pct
FROM raw
GROUP BY Country
HAVING invoices >= 200
ORDER BY cancel_rate_pct DESC;
