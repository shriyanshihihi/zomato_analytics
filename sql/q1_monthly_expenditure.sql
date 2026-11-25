-- ============================================================
-- CV bullet 1: 'SQL aggregation queries ... expenditure patterns'
-- QUESTION   : How much did customers spend each month, and how often did they order?
-- HOW        : Collapses ~19k order rows into 9 monthly rows (GROUP BY month) with COUNT, COUNT(DISTINCT), SUM, AVG.
-- READ IT AS : Look at: gmv, aov, orders_per_active_user. Rising orders_per_active_user = habit forming.
-- SAY IN INTERVIEW: 'I used GROUP BY month with COUNT DISTINCT users so active users are not double counted.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
-- Q1 Expenditure pattern over time (monthly). SYNTHETIC DATA.
-- Aggregation: COUNT / COUNT DISTINCT / SUM / AVG with GROUP BY month.
SELECT strftime('%Y-%m', order_date)                         AS month,
       COUNT(*)                                              AS orders,
       COUNT(DISTINCT user_id)                               AS active_users,
       ROUND(SUM(order_value), 0)                            AS gmv,
       ROUND(AVG(order_value), 1)                            AS aov,
       ROUND(SUM(delivery_fee), 0)                           AS delivery_fees_paid,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT user_id), 2)    AS orders_per_active_user,
       ROUND(SUM(order_value) / COUNT(DISTINCT user_id), 0)  AS spend_per_active_user
FROM orders
GROUP BY 1
ORDER BY 1;
