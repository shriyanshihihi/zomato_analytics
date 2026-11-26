-- ============================================================
-- CV bullet 2: 'cohort analysis'
-- QUESTION   : Of users who started in month X, how many still order N months later?
-- HOW        : CTEs: first order month = cohort; distinct active months; month_offset arithmetic; GROUP BY cohort, offset.
-- READ IT AS : retention_pct is the share of the cohort still ordering; Python only pivots it into a heatmap grid.
-- SAY IN INTERVIEW: 'Cohort = month of first order, so month 0 is 100% by definition.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
-- Q5 Cohort table. Cohort = month of a user's FIRST ORDER. month_offset = months since that month.
-- Output is "long" (cohort, month_offset, retention_pct); it is already the finished retention number.
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
       COUNT(DISTINCT a.user_id) AS active_users,
       ROUND(100.0 * COUNT(DISTINCT a.user_id) / s.cohort_size, 1) AS retention_pct   -- the retention % itself, in SQL
FROM first_order f
JOIN sizes s    ON s.cohort = f.cohort
JOIN activity a ON a.user_id = f.user_id
GROUP BY f.cohort, s.cohort_size, month_offset
ORDER BY f.cohort, month_offset;
