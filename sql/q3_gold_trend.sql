-- Q3 Gold subscription trend per month (uses the helper `months` table).
-- new_gold   = first-term subscriptions starting in the month (new + returning members)
-- active_gold= members whose term covers the month end
-- lapsed     = terms that ended in the month and were NOT renewed
WITH t AS (
  SELECT m.month,
    (SELECT COUNT(*) FROM subscriptions s
      WHERE s.is_renewal_term = 0 AND s.start_date BETWEEN m.month_start AND m.month_end)  AS new_gold,
    (SELECT COUNT(DISTINCT s.user_id) FROM subscriptions s
      WHERE s.start_date <= m.month_end AND s.end_date >= m.month_end)                      AS active_gold,
    (SELECT COUNT(*) FROM subscriptions s
      WHERE s.renewed_next = 0 AND s.end_date BETWEEN m.month_start AND m.month_end)       AS lapsed,
    (SELECT COUNT(*) FROM subscriptions s
      WHERE s.renewed_next IS NOT NULL AND s.end_date BETWEEN m.month_start AND m.month_end) AS decided_terms,
    (SELECT COUNT(DISTINCT o.user_id) FROM orders o
      WHERE strftime('%Y-%m', o.order_date) = m.month)                                      AS active_users,
    (SELECT COUNT(*) FROM users u WHERE u.signup_date <= m.month_end)                       AS registered_users
  FROM months m
)
SELECT month, new_gold, active_gold, lapsed, decided_terms, active_users, registered_users,
       ROUND(100.0 * active_gold / registered_users, 2) AS gold_penetration_pct
FROM t ORDER BY month;
