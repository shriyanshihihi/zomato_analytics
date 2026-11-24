"""Cohort analysis, affinity analysis and retention-lever identification (pandas)."""
import math

import numpy as np
import pandas as pd


# ----------------------------------------------------------------- cohort analysis
def retention_matrix(cohort_long):
    """Long (cohort, cohort_size, month_offset, active_users) -> retention % matrix."""
    piv = cohort_long.pivot(index="cohort", columns="month_offset", values="active_users")
    sizes = cohort_long.drop_duplicates("cohort").set_index("cohort")["cohort_size"]
    ret = piv.div(sizes, axis=0) * 100
    # offsets that have not happened yet for late cohorts stay NaN (not 0!)
    return ret.round(1), sizes


# ----------------------------------------------------------------- affinity analysis
def cuisine_affinity(orders, min_support=0.03):
    """Market-basket style: basket = set of cuisines a user ever ordered.
    support(A,B) = P(A and B); confidence(A->B) = P(B|A); lift = confidence / P(B)."""
    m = pd.crosstab(orders["user_id"], orders["cuisine"]).gt(0).astype(int)
    n = len(m)
    co = m.T.dot(m)
    rows = []
    for a in m.columns:
        for b in m.columns:
            if a == b:
                continue
            sup = co.loc[a, b] / n
            if sup < min_support:
                continue
            conf = co.loc[a, b] / co.loc[a, a]
            lift = conf / (co.loc[b, b] / n)
            rows.append((a, b, round(sup, 3), round(conf, 3), round(lift, 3)))
    out = pd.DataFrame(rows, columns=["if_ordered", "then_ordered", "support", "confidence", "lift"])
    return out.sort_values("lift", ascending=False).reset_index(drop=True)


# Candidate behaviours measured in the first 30 days. kind:
#   activate = nudge users who do NOT show the behaviour to start showing it
#   target   = send a Gold pitch/offer to users who already show it
CANDIDATES = {
    "Early frequency (3+ orders in 30d)": ("activate", lambda d: d.early_orders >= 3),
    "Fee burden (Rs150+ fees in 30d)":     ("target",   lambda d: d.early_fees >= 150),
    "Cuisine discovery (3+ cuisines)":     ("activate", lambda d: d.early_cuisines >= 3),
    "Late-night ordering":                 ("target",   lambda d: d.had_late_night == 1),
    "Offer-driven (discount >= 10%)":      ("target",   lambda d: d.disc_share >= 0.10),
}


def _z_two_prop(x1, n1, x2, n2):
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) or 1e-9
    return (x1 / n1 - x2 / n2) / se


def behaviour_affinity(feat):
    """Affinity of each behaviour with joining Gold in days 30-90 (lift + significance)."""
    d = feat[feat.gold_in_window == 0].copy()
    base = d.gold_30_90d.mean()
    rows = []
    for name, (kind, fn) in CANDIDATES.items():
        b = fn(d)
        n1, n0 = int(b.sum()), int((~b).sum())
        if n1 == 0 or n0 == 0:
            continue
        x1, x0 = int(d.gold_30_90d[b].sum()), int(d.gold_30_90d[~b].sum())
        rows.append(dict(behaviour=name, kind=kind, n_with=n1, n_without=n0,
                         pct_users=round(100 * n1 / len(d), 1),
                         gold_rate_with=round(100 * x1 / n1, 2),
                         gold_rate_without=round(100 * x0 / n0, 2),
                         lift=round((x1 / n1) / base, 2),
                         z=round(_z_two_prop(x1, n1, x0, n0), 2)))
    return pd.DataFrame(rows), base, len(d), int(d.gold_30_90d.sum())


def lever_conversion_impact(aff, baseline_conversions, capture=0.20, uplift=0.25):
    """Convert behaviour affinity into an ASSUMPTION-BASED relative uplift u of new-Gold flow.
    activate: capture% of users without the behaviour start behaving like those with it.
    target  : the pitch raises conversion of users WITH the behaviour by `uplift` (relative)."""
    out = []
    for _, r in aff.iterrows():
        rate_w, rate_wo = r.gold_rate_with / 100, r.gold_rate_without / 100
        if r.kind == "activate":
            extra = capture * r.n_without * max(rate_w - rate_wo, 0)
        else:
            extra = uplift * r.n_with * rate_w
        out.append(dict(r, extra_conversions=round(extra, 1),
                        u_new_gold=extra / baseline_conversions if baseline_conversions else 0))
    return pd.DataFrame(out)


def renewal_lever(renewal_df, capture=0.20):
    """Gold retention lever: move `capture` of low-usage terms to the high-usage band's renewal rate."""
    df = renewal_df.copy()
    total = df.terms.sum()
    r0 = df.renewed.sum() / total
    hi = df.iloc[-1]
    hi_rate = hi.renewed / hi.terms
    low = df[df.index != df.index[-1]]
    low_share = low.terms.sum() / total
    low_rate = low.renewed.sum() / low.terms.sum()
    delta = capture * low_share * max(hi_rate - low_rate, 0)
    rho = delta / (1 - r0) if r0 < 1 else 0           # relative cut in churn
    return dict(renewal_rate=r0, hi_rate=hi_rate, low_rate=low_rate, low_share=low_share,
                delta_renewal=delta, churn_reduction_rho=rho)
