-- Q4 Gold vs Non-Gold order behaviour. CAUTION: selection bias - people who join Gold may already
-- be heavy users, so this is a description, not proof that Gold CAUSES more orders.
WITH o2 AS (
  SELECT *, user_id || '|' || strftime('%Y-%m', order_date) AS user_month FROM orders
)
SELECT CASE WHEN is_gold_order = 1 THEN 'Gold' ELSE 'Non-Gold' END AS status,
       COUNT(*)                                       AS orders,
       COUNT(DISTINCT user_month)                     AS user_months,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT user_month), 2) AS orders_per_user_month,
       ROUND(AVG(order_value), 1)                     AS aov,
       ROUND(AVG(delivery_fee), 1)                    AS avg_delivery_fee,
       ROUND(AVG(discount_amt), 1)                    AS avg_discount
FROM o2
GROUP BY 1
ORDER BY 1;
