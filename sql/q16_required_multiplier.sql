-- ============================================================
-- CV bullet 2: '30% Gold subscriber growth' is a TARGET. This asks: how strong must the top-3 levers be to reach it?
-- Smallest strength k (as a multiple of the assumed lever effects) whose growth reaches :target percent.
-- 0 = the baseline alone already reaches it; NULL = not reachable within 3x.
-- SAY IN INTERVIEW: '30% was the target I tested; the output is how much the levers must deliver to get there.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
SELECT CASE
  WHEN (SELECT growth_pct FROM sim_result WHERE scenario = 'Baseline (no levers)' AND t = :horizon) >= :target THEN 0.0
  ELSE (SELECT MIN(CAST(substr(scenario, 6) AS REAL)) FROM sim_result
        WHERE scenario LIKE 'grid_%' AND t = :horizon AND growth_pct >= :target)
  END AS multiplier_needed;
