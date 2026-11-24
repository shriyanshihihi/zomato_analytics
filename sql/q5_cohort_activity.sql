-- Q5 Cohort table. Cohort = month of a user's FIRST ORDER. month_offset = months since that month.
-- Output is "long" (cohort, month_offset, active_users); pandas pivots it into the retention matrix.
WITH first_order AS (
  SELECT user_id, strftime('%Y-%m', MIN(order_date)) AS cohort FROM orders GROUP BY user_id
),
sizes AS (SELECT cohort, COUNT(*) AS cohort_size FROM first_order GROUP BY cohort),
activity AS (
  SELECT DISTINCT user_id, strftime('%Y-%m', order_date) AS act_month FROM orders
)
SELECT f.cohort,
       s.cohort_size,
       (CAST(substr(a.act_month, 1, 4) AS INT) * 12 + CAST(substr(a.act_month, 6, 2) AS INT))
     - (CAST(substr(f.cohort, 1, 4) AS INT) * 12 + CAST(substr(f.cohort, 6, 2) AS INT)) AS month_offset,
       COUNT(DISTINCT a.user_id) AS active_users
FROM first_order f
JOIN sizes s    ON s.cohort = f.cohort
JOIN activity a ON a.user_id = f.user_id
GROUP BY f.cohort, s.cohort_size, month_offset
ORDER BY f.cohort, month_offset;
