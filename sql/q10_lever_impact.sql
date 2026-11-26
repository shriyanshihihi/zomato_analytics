-- ============================================================
-- CV bullet 2: '3 actionable retention levers' - turn evidence into candidate levers
-- QUESTION   : If we acted on each behaviour, how many extra Gold joiners (relative to today) might we get?
-- HOW        : two lever types.
--   activate: capture% of users WITHOUT the behaviour start behaving like those with it
--             extra = capture * n_without * (rate_with - rate_without)
--   target  : a Gold pitch lifts conversion of users WITH the behaviour by `uplift` (relative)
--             extra = uplift * n_with * rate_with
--   u = extra / today's Gold joiners  (relative uplift of new-Gold flow)
--   renewal lever (retention): move `capture` of low-usage Gold terms to the high-usage renewal rate;
--             rho = relative cut in the share of members who lapse.
-- ASSUMPTIONS (not measured): :capture and :uplift are passed in (defaults 0.20 / 0.25).
-- SAY IN INTERVIEW: 'Each lever has a user group, an action and an estimated size; the sizes are assumptions to be A/B tested.'
-- (all data is SYNTHETIC demo data)
-- ============================================================
CREATE TABLE lever_impact AS
WITH base AS (SELECT SUM(gold_30_90d) AS conv FROM user_features WHERE gold_in_window = 0),
acq AS (
  SELECT a.behaviour AS name, 'acquisition (' || a.kind || ')' AS type,
         CASE WHEN a.kind = 'activate'
              THEN :capture * a.n_without * MAX(a.rate_with - a.rate_without, 0)
              ELSE :uplift  * a.n_with * a.rate_with END AS extra_conversions,
         a.z AS z, a.lift AS lift
  FROM affinity a),
tot AS (SELECT SUM(terms) AS terms, SUM(renewed) AS renewed FROM renewal_bands),
hi  AS (SELECT 1.0 * renewed / terms AS rate FROM renewal_bands WHERE usage_band LIKE '3:%'),
lo  AS (SELECT SUM(terms) AS terms, SUM(renewed) AS renewed FROM renewal_bands WHERE usage_band NOT LIKE '3:%')
SELECT name, type, extra_conversions, extra_conversions / base.conv AS u, 0.0 AS rho, z, lift FROM acq, base
UNION ALL
SELECT 'Gold renewal engagement (2+ orders/month)', 'retention (renewal)', NULL, 0.0,
       (:capture * (1.0 * lo.terms / tot.terms) * MAX(hi.rate - 1.0 * lo.renewed / lo.terms, 0))
         / (1 - 1.0 * tot.renewed / tot.terms),
       NULL, NULL
FROM tot, hi, lo;
