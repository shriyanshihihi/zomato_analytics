-- ============================================================
-- CV bullet 2: 'Identified 3 actionable retention levers'  <- THIS is where the 3 come from
-- HOW        : each candidate was simulated ALONE (table sim_standalone). gain_pct = its growth minus baseline growth.
--              Keep only statistically meaningful ones (z >= 2; the renewal lever has no z), rank by gain, take top 3.
-- SAY IN INTERVIEW: 'I tested each idea on its own in the projection, kept the ones backed by evidence, and took the top three.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
CREATE TABLE lever_ranking AS
WITH g AS (
  SELECT l.name, l.type, l.u, l.rho, l.z, l.lift,
         ROUND(s.growth_pct - b.growth_pct, 2) AS gain_pct,
         CASE WHEN l.z IS NULL OR l.z >= 2 THEN 1 ELSE 0 END AS significant
  FROM lever_impact l
  JOIN sim_standalone s ON s.scenario = l.name AND s.t = :horizon
  JOIN sim_standalone b ON b.scenario = 'Baseline (no levers)' AND b.t = :horizon),
r AS (SELECT name, ROW_NUMBER() OVER (ORDER BY gain_pct DESC) AS rnk FROM g WHERE significant = 1)
SELECT g.*, r.rnk, CASE WHEN r.rnk <= 3 THEN 1 ELSE 0 END AS is_top3
FROM g LEFT JOIN r ON r.name = g.name;
