-- Q7 Gold renewal rate by how much the member ordered during the term (only decided terms).
WITH term_usage AS (
  SELECT s.sub_id, s.renewed_next, COUNT(o.order_id) AS term_orders
  FROM subscriptions s
  LEFT JOIN orders o ON o.user_id = s.user_id AND o.order_date BETWEEN s.start_date AND s.end_date
  WHERE s.renewed_next IS NOT NULL
  GROUP BY s.sub_id, s.renewed_next
)
SELECT CASE WHEN term_orders >= 6 THEN '3: 6+ orders (2+/month)'
            WHEN term_orders >= 3 THEN '2: 3-5 orders'
            ELSE '1: 0-2 orders' END AS usage_band,
       COUNT(*)                      AS terms,
       SUM(renewed_next)             AS renewed,
       ROUND(100.0 * AVG(renewed_next), 1) AS renewal_rate_pct
FROM term_usage
GROUP BY 1
ORDER BY 1;
