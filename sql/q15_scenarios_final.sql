-- Final scenario table: baseline, and the TOP-3 levers together at cautious / expected / optimistic strength,
-- plus a grid of strengths k = 0.00 ... 3.00 (step 0.02) used to find how strong the levers must be to hit the target.
-- SYNTHETIC demo data.
CREATE TABLE scenarios AS
WITH RECURSIVE tot AS (SELECT SUM(u) AS u, SUM(rho) AS rho FROM lever_ranking WHERE is_top3 = 1),
ks(k) AS (SELECT 0.0 UNION ALL SELECT ROUND(k + 0.02, 2) FROM ks WHERE k < 3.0)
SELECT 'Baseline (no levers)' AS name, 0.0 AS u, 0.0 AS rho, 1.0 AS k
UNION ALL SELECT 'Conservative', u, rho, 0.5 FROM tot
UNION ALL SELECT 'Base',         u, rho, 1.0 FROM tot
UNION ALL SELECT 'Optimistic',   u, rho, 1.5 FROM tot
UNION ALL SELECT 'grid_' || k, tot.u, tot.rho, k FROM ks, tot;
