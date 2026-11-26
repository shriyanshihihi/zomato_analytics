-- ============================================================
-- CV bullet 2: 'affinity analysis' -> evidence for the 3 levers
-- QUESTION   : Which first-30-day behaviours go together with joining Gold in days 30-90?
-- HOW        : view `user_features` (q6) -> one flag per candidate behaviour -> compare Gold rate with vs without.
-- READ IT AS : lift = (Gold rate WITH behaviour) / (overall Gold rate). Lift 2 = twice as likely.
--              z = how many standard errors apart the two rates are; z >= 2 means probably not chance.
-- SAY IN INTERVIEW: 'Customers who tried several cuisines early joined Gold about twice as often as average.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
CREATE TABLE affinity AS
WITH d AS (SELECT * FROM user_features WHERE gold_in_window = 0),     -- ignore users already Gold in the window
flags AS (
  SELECT 'Early frequency (3+ orders in 30d)' AS behaviour, 'activate' AS kind, (early_orders >= 3)    AS b, gold_30_90d AS y FROM d
  UNION ALL SELECT 'Fee burden (Rs150+ fees in 30d)',        'target',   (early_fees >= 150),           gold_30_90d FROM d
  UNION ALL SELECT 'Cuisine discovery (3+ cuisines)',        'activate', (early_cuisines >= 3),         gold_30_90d FROM d
  UNION ALL SELECT 'Late-night ordering',                    'target',   (had_late_night = 1),          gold_30_90d FROM d
  UNION ALL SELECT 'Offer-driven (discount >= 10%)',         'target',   (disc_share >= 0.10),          gold_30_90d FROM d),
agg AS (
  SELECT behaviour, kind, COUNT(*) AS n, SUM(y) AS x,
         SUM(b) AS n_with, SUM(1 - b) AS n_without, SUM(b * y) AS x_with, SUM((1 - b) * y) AS x_without
  FROM flags GROUP BY behaviour, kind),
rates AS (
  SELECT *, 1.0 * x_with / n_with AS rate_with, 1.0 * x_without / n_without AS rate_without,
            1.0 * x / n AS base_rate, 1.0 * x / n AS p_pool FROM agg)
SELECT behaviour, kind, n_with, n_without,
       rate_with, rate_without, base_rate,
       rate_with / base_rate AS lift,
       (rate_with - rate_without) / sqrt(p_pool * (1 - p_pool) * (1.0 / n_with + 1.0 / n_without)) AS z
FROM rates;
