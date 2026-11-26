-- ============================================================
-- CV bullet 2: 'simulate roadmap' - the STARTING POINT, read straight from the Gold trend (view gold_trend = q3)
-- G0 = Gold members at the latest month end; n0 = average new Gold members per month (last 3 months);
-- g  = monthly lapse rate = lapsed / active members at the previous month end (last 3 months).
-- SAY IN INTERVIEW: 'The projection starts from the real current Gold base, joiners and lapse rate.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
WITH t AS (
  SELECT month, active_gold, new_gold, lapsed,
         LAG(active_gold) OVER (ORDER BY month) AS prev_active
  FROM gold_trend),
last3 AS (SELECT * FROM t ORDER BY month DESC LIMIT 3)
SELECT (SELECT active_gold FROM t ORDER BY month DESC LIMIT 1) AS G0,
       AVG(new_gold)                                          AS n0,
       1.0 * SUM(lapsed) / SUM(prev_active)                   AS g
FROM last3;
