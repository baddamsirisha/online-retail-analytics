-- 07_cohorts.sql : monthly acquisition cohorts and how many customers come back
WITH first AS (
  SELECT customer_id, MIN(month) AS cohort FROM sales
  WHERE customer_id IS NOT NULL GROUP BY customer_id
),
activity AS (
  SELECT DISTINCT s.customer_id, f.cohort, s.month
  FROM sales s JOIN first f USING (customer_id)
)
SELECT cohort,
       (CAST(substr(month,1,4) AS INTEGER) - CAST(substr(cohort,1,4) AS INTEGER)) * 12
       + (CAST(substr(month,6,2) AS INTEGER) - CAST(substr(cohort,6,2) AS INTEGER)) AS months_since_first,
       COUNT(*) AS customers
FROM activity
GROUP BY cohort, months_since_first
ORDER BY cohort, months_since_first;
