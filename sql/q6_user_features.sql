-- Q6 One row per user: behaviour in the FIRST 30 DAYS (features) and whether they joined Gold in
-- days 30-90 (outcome). Features and outcome are separated in time on purpose, to avoid leakage /
-- reverse causality (e.g. Gold members pay 0 delivery fee, which would fake a "low fee" signal).
-- Only users with a full 90-day follow-up (first order on/before 2025-06-30) are kept.
WITH first_order AS (
  SELECT user_id, MIN(order_date) AS first_dt FROM orders GROUP BY user_id
),
win AS (
  SELECT o.*, f.first_dt FROM orders o JOIN first_order f ON f.user_id = o.user_id
  WHERE o.order_date < date(f.first_dt, '+30 days')
),
feat AS (
  SELECT user_id, first_dt,
         COUNT(*)                      AS early_orders,
         SUM(order_value)              AS early_value,
         SUM(delivery_fee)             AS early_fees,
         SUM(discount_amt)             AS early_disc,
         COUNT(DISTINCT cuisine)       AS early_cuisines,
         MAX(CASE WHEN daypart = 'late_night' THEN 1 ELSE 0 END) AS had_late_night
  FROM win GROUP BY user_id, first_dt
)
SELECT f.user_id, f.first_dt, f.early_orders, f.early_cuisines, f.had_late_night, f.early_fees,
       ROUND(1.0 * f.early_fees / f.early_value, 4) AS fee_share,
       ROUND(1.0 * f.early_disc / f.early_value, 4) AS disc_share,
       CASE WHEN EXISTS (SELECT 1 FROM subscriptions s WHERE s.user_id = f.user_id
                          AND s.start_date < date(f.first_dt, '+30 days')) THEN 1 ELSE 0 END AS gold_in_window,
       CASE WHEN EXISTS (SELECT 1 FROM subscriptions s WHERE s.user_id = f.user_id AND s.is_renewal_term = 0
                          AND s.start_date >= date(f.first_dt, '+30 days')
                          AND s.start_date <  date(f.first_dt, '+90 days')) THEN 1 ELSE 0 END AS gold_30_90d
FROM feat f
WHERE f.first_dt <= '2025-06-30';
