-- ============================================================
-- CV bullet 1: 'expenditure patterns' (who spends)
-- QUESTION   : Is spend evenly spread, or do a few customers give most of it? Are big spenders more often Gold?
-- HOW        : JOIN users->orders, LEFT JOIN a DISTINCT Gold list, NTILE(4) window function to rank users into 4 spend tiers.
-- READ IT AS : Look at: pct_of_total_spend (top tier gives most), pct_ever_gold (rises with spend), fees_pct_of_spend.
-- SAY IN INTERVIEW: 'Spend is skewed, so I segmented into quartiles instead of trusting the average.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
-- Q2 Expenditure patterns by customer: split users into 4 spend quartiles (window function NTILE).
-- Joins: users -> orders (1:many), LEFT JOIN to a DISTINCT list of Gold users (avoids row multiplication).
WITH ever_gold AS (SELECT DISTINCT user_id FROM subscriptions),
user_spend AS (
  SELECT u.user_id,
         COUNT(o.order_id)   AS orders,
         SUM(o.order_value)  AS spend,
         SUM(o.delivery_fee) AS fees,
         CASE WHEN g.user_id IS NOT NULL THEN 1 ELSE 0 END AS is_gold
  FROM users u
  JOIN orders o ON o.user_id = u.user_id
  LEFT JOIN ever_gold g ON g.user_id = u.user_id
  GROUP BY u.user_id
),
ranked AS (SELECT *, NTILE(4) OVER (ORDER BY spend) AS q FROM user_spend)
SELECT q                                                          AS spend_quartile,   -- 4 = top spenders
       COUNT(*)                                                   AS users,
       ROUND(AVG(orders), 1)                                      AS avg_orders,
       ROUND(AVG(spend), 0)                                       AS avg_spend,
       ROUND(100.0 * SUM(spend) / (SELECT SUM(spend) FROM user_spend), 1) AS pct_of_total_spend,
       ROUND(100.0 * AVG(is_gold), 1)                             AS pct_ever_gold,
       ROUND(100.0 * SUM(fees) / SUM(spend), 1)                   AS fees_pct_of_spend
FROM ranked
GROUP BY q
ORDER BY q;
