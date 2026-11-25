"""Roadmap simulation for Gold subscriber growth.

CV link: "simulate roadmap for 30% Gold subscriber growth".
PLAIN ENGLISH: start with today's Gold members. Each month some lapse and some new ones join.
Levers add extra joiners (or cut lapses) gradually. Run it forward and see the growth %.
The 30% is a TARGET we test against, not an achieved result. required_multiplier() answers
"how strong must the levers be to hit it?"


Model (monthly steps, t = 1..H):
    G[t] = G[t-1] * (1 - g_eff[t]) + n0 * (1 + ramp[t] * k * sum(u_i))
    g_eff[t] = g * (1 - ramp[t] * k * rho)
G = active Gold members, n0 = baseline new Gold members per month, g = monthly lapse rate,
u_i = relative uplift of new-Gold flow from acquisition lever i, rho = relative churn cut from the
renewal lever, ramp = linear roll-out over `ramp_months`, k = scenario multiplier on lever effect.
ASSUMPTIONS (stated, not measured): flat acquisition inflow, no seasonality, levers add up, effects
phase in linearly.
"""


def project(G0, n0, g, u_sum=0.0, rho=0.0, k=1.0, horizon=6, ramp_months=3):
    G, path = G0, [G0]
    for t in range(1, horizon + 1):
        ramp = min(1.0, t / ramp_months)
        g_eff = g * (1 - ramp * k * rho)
        G = G * (1 - g_eff) + n0 * (1 + ramp * k * u_sum)
        path.append(G)
    return path


def growth_pct(path):
    return 100 * (path[-1] / path[0] - 1)


def required_multiplier(G0, n0, g, u_sum, rho, target_pct=30.0, horizon=6, kmax=50):
    """Smallest k (scaling of the assumed lever effects) that reaches target growth; None if unreachable."""
    if growth_pct(project(G0, n0, g, 0, 0, 1, horizon)) >= target_pct:
        return 0.0
    if growth_pct(project(G0, n0, g, u_sum, rho, kmax, horizon)) < target_pct:
        return None
    lo, hi = 0.0, float(kmax)
    for _ in range(60):
        mid = (lo + hi) / 2
        if growth_pct(project(G0, n0, g, u_sum, rho, mid, horizon)) >= target_pct:
            hi = mid
        else:
            lo = mid
    return round(hi, 2)
