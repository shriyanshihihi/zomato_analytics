-- Scenario table for ranking: baseline + each candidate lever ALONE at normal strength (k = 1). SYNTHETIC demo.
CREATE TABLE scenarios AS
SELECT 'Baseline (no levers)' AS name, 0.0 AS u, 0.0 AS rho, 1.0 AS k
UNION ALL
SELECT name, u, rho, 1.0 FROM lever_impact;
