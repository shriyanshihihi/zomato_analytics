-- ============================================================
-- CV bullet 2: 'simulate roadmap for 30% Gold subscriber growth'
-- QUESTION   : Month by month, how many Gold members will there be, with and without the levers?
-- HOW        : a recursive query (each month is computed from the previous month):
--     members(t) = members(t-1) * (1 - g * (1 - ramp*k*rho))  +  n0 * (1 + ramp*k*u)
--     g = lapse rate, n0 = baseline joiners, u / rho = lever effects, ramp = gradual roll-out (t / ramp_months, max 1),
--     k = scenario strength (0.5 cautious, 1 expected, 1.5 optimistic).
-- ASSUMPTIONS: flat joiner inflow, no seasonality, lever effects simply add up. Lever sizes are assumed, not measured.
-- Reads the `scenarios` table (name, u, rho, k). Parameters: G0, n0, g, horizon, ramp.
-- SAY IN INTERVIEW: 'A simple month-by-month projection; the 30% is the target I compared it with.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
CREATE TABLE sim_result AS
WITH RECURSIVE sim(scenario, t, members) AS (
  SELECT name, 0, :G0 FROM scenarios
  UNION ALL
  SELECT s.scenario, s.t + 1,
         s.members * (1 - :g * (1 - MIN(1.0, (s.t + 1) * 1.0 / :ramp) * sc.k * sc.rho))
         + :n0 * (1 + MIN(1.0, (s.t + 1) * 1.0 / :ramp) * sc.k * sc.u)
  FROM sim s JOIN scenarios sc ON sc.name = s.scenario
  WHERE s.t < :horizon)
SELECT scenario, t, members, 100.0 * (members / :G0 - 1) AS growth_pct FROM sim;
