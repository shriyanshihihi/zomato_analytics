-- ============================================================
-- CV bullet 2: 'affinity analysis' (which cuisines go together)
-- QUESTION   : If a customer orders cuisine A, how much more likely are they to also order cuisine B?
-- HOW        : self-join of (user, cuisine) pairs; support / confidence / lift all computed in SQL.
-- READ IT AS : support = share of users with both; confidence = of A-users, share also B; lift > 1 = go together.
-- SAY IN INTERVIEW: 'I counted how often two cuisines are ordered by the same customer, compared with chance.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
WITH uc AS (SELECT DISTINCT user_id, cuisine FROM orders),
n  AS (SELECT COUNT(DISTINCT user_id) AS total FROM orders),
cnt AS (SELECT cuisine, COUNT(*) AS users FROM uc GROUP BY cuisine),
pairs AS (
  SELECT a.cuisine AS a, b.cuisine AS b, COUNT(*) AS both_users
  FROM uc a JOIN uc b ON a.user_id = b.user_id AND a.cuisine <> b.cuisine
  GROUP BY a.cuisine, b.cuisine)
SELECT p.a AS if_ordered, p.b AS then_ordered,
       ROUND(1.0 * p.both_users / n.total, 3)                                  AS support,
       ROUND(1.0 * p.both_users / ca.users, 3)                                 AS confidence,
       ROUND((1.0 * p.both_users / ca.users) / (1.0 * cb.users / n.total), 3)  AS lift
FROM pairs p JOIN cnt ca ON ca.cuisine = p.a JOIN cnt cb ON cb.cuisine = p.b, n
WHERE 1.0 * p.both_users / n.total >= 0.03
ORDER BY lift DESC
LIMIT 15;
