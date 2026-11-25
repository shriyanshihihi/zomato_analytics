"""Entry point.  python main.py            (about 10 seconds)

Read docs/PROJECT_WALKTHROUGH.md first - it explains every step in plain English.
Pipeline: synthetic data -> SQLite -> SQL queries -> cohort/affinity -> levers -> simulation -> outputs.
ALL NUMBERS PRODUCED ARE FROM SYNTHETIC DEMO DATA. They are not real results and not the CV's results.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from analysis import (behaviour_affinity, cuisine_affinity, lever_conversion_impact,  # noqa: E402
                      renewal_lever, retention_matrix)
from data_gen import generate  # noqa: E402
from database import build_db, run_sql  # noqa: E402
from simulate import growth_pct, project, required_multiplier  # noqa: E402
import viz  # noqa: E402

TARGET = 30.0
HORIZON = 3  # months in the roadmap (one quarter)
SCENARIOS = {"Conservative": 0.5, "Base": 1.0, "Optimistic": 1.5}


def main(n_users, seed, outdir, capture, uplift):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    (ROOT / "data").mkdir(exist_ok=True)
    print(f"[1/7] Generating SYNTHETIC data: {n_users} users, seed={seed}  (stand-in for real tables: users, orders, subscriptions)")
    users, orders, subs = generate(n_users, seed)
    for name, df in (("users", users), ("orders", orders), ("subscriptions", subs)):
        df.to_csv(ROOT / "data" / f"{name}.csv", index=False)

    print("[2/7] Loading into SQLite")
    con = build_db(users, orders, subs, str(out / "demo.db"))

    print("[3/7] Running SQL aggregation queries  <- CV bullet 1: expenditure patterns + Gold trends")
    q1, q2 = run_sql(con, "q1_monthly_expenditure.sql"), run_sql(con, "q2_spend_quartiles.sql")
    q3, q4 = run_sql(con, "q3_gold_trend.sql"), run_sql(con, "q4_gold_vs_nongold.sql")
    q5, q6 = run_sql(con, "q5_cohort_activity.sql"), run_sql(con, "q6_user_features.sql")
    q7 = run_sql(con, "q7_renewal_by_usage.sql")
    for n, d in (("q1_monthly_expenditure", q1), ("q2_spend_quartiles", q2), ("q3_gold_trend", q3),
                 ("q4_gold_vs_nongold", q4), ("q5_cohort_activity", q5), ("q6_user_features", q6),
                 ("q7_renewal_by_usage", q7)):
        d.to_csv(out / f"{n}.csv", index=False)

    print("[4/7] Cohort + affinity analysis  <- CV bullet 2: cohort & affinity analysis")
    ret, sizes = retention_matrix(q5)
    ret.to_csv(out / "cohort_retention_matrix.csv")
    aff, base_rate, n_elig, base_conv = behaviour_affinity(q6)
    cuisines = cuisine_affinity(orders)
    cuisines.head(15).to_csv(out / "cuisine_affinity_top15.csv", index=False)

    print("[5/7] Ranking levers  <- CV bullet 2: '3 actionable retention levers' (top 3 by simulated gain)")
    imp = lever_conversion_impact(aff, base_conv, capture, uplift)
    ren = renewal_lever(q7.set_index("usage_band"), capture)

    # baseline parameters for the simulation, taken from SQL output (last 3 months)
    last3 = q3.tail(3).reset_index(drop=True)
    prev_active = q3.active_gold.shift(1).tail(3).reset_index(drop=True)
    G0 = int(q3.active_gold.iloc[-1])
    n0 = float(last3.new_gold.mean())
    g = float(last3.lapsed.sum() / prev_active.sum())
    base_growth = growth_pct(project(G0, n0, g, horizon=HORIZON))

    cand = []
    for _, r in imp.iterrows():
        gain = growth_pct(project(G0, n0, g, u_sum=r.u_new_gold, horizon=HORIZON)) - base_growth
        cand.append(dict(name=r.behaviour, type=f"acquisition ({r.kind})", gain_pct=gain, u=r.u_new_gold,
                         rho=0.0, z=r.z, lift=r.lift))
    gain_r = growth_pct(project(G0, n0, g, rho=ren["churn_reduction_rho"], horizon=HORIZON)) - base_growth
    cand.append(dict(name="Gold renewal engagement (2+ orders/month)", type="retention (renewal)",
                     gain_pct=gain_r, u=0.0, rho=ren["churn_reduction_rho"], z=None, lift=None))
    cand = pd.DataFrame(cand)
    # keep only statistically meaningful acquisition levers (|z| >= 2), then take top 3 by gain
    ok = cand[(cand.z.isna()) | (cand.z >= 2)].sort_values("gain_pct", ascending=False)
    top3 = ok.head(3)
    cand.round(3).to_csv(out / "lever_candidates.csv", index=False)

    print("[6/7] Simulating roadmap (3 months)  <- CV bullet 2: 'simulate roadmap for 30% Gold growth' (a TARGET, not a result)")
    u_sum, rho = float(top3.u.sum()), float(top3.rho.sum())
    paths = {"Baseline (no levers)": project(G0, n0, g, horizon=HORIZON)}
    results = {"Baseline (no levers)": round(base_growth, 1)}
    for name, k in SCENARIOS.items():
        paths[name] = project(G0, n0, g, u_sum, rho, k, horizon=HORIZON)
        results[name] = round(growth_pct(paths[name]), 1)
    k_req = required_multiplier(G0, n0, g, u_sum, rho, TARGET, HORIZON)

    print("[7/7] Writing charts + summary")
    viz.cohort_heatmap(ret, out / "chart_cohort_retention.png")
    viz.gold_trend(q3, out / "chart_gold_trend.png")
    viz.spend_quartiles(q2, out / "chart_spend_quartiles.png")
    viz.lever_chart(cand, set(top3.name), out / "chart_levers.png")
    viz.scenarios(paths, G0 * (1 + TARGET / 100), out / "chart_simulation.png")
    viz.architecture(ROOT / "docs" / "architecture.png")
    viz.workflow(ROOT / "docs" / "workflow.png")

    summary = dict(
        DISCLAIMER="SYNTHETIC DEMO DATA - not real Zomato data, not the CV's real results",
        users=n_users, orders=len(orders), gold_terms=len(subs),
        eligible_users_for_affinity=n_elig, baseline_gold_conversion_30_90d_pct=round(100 * base_rate, 2),
        baseline_gold_members_G0=G0, baseline_new_gold_per_month_n0=round(n0, 1),
        monthly_gold_lapse_rate_g=round(g, 4), renewal_rate_pct=round(100 * ren["renewal_rate"], 1),
        assumptions=dict(capture=capture, uplift=uplift, ramp_months=3, horizon_months=HORIZON),
        top3_levers=top3[["name", "type", "gain_pct"]].round(2).to_dict("records"),
        growth_pct_by_scenario=results, target_pct=TARGET,
        multiplier_on_lever_effects_needed_for_target=k_req,
    )
    (out / "results.json").write_text(json.dumps(summary, indent=2, default=float))
    print("\n=== SUMMARY (synthetic data) ===")
    print(json.dumps(summary, indent=2, default=float))
    print(f"\nFiles written to: {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--users", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--outdir", default=str(ROOT / "outputs"))
    ap.add_argument("--capture", type=float, default=0.20, help="assumed share of users a nudge moves (0-1)")
    ap.add_argument("--uplift", type=float, default=0.25, help="assumed relative uplift of a targeted pitch")
    a = ap.parse_args()
    try:
        main(a.users, a.seed, a.outdir, a.capture, a.uplift)
    except Exception as exc:  # basic, readable error handling
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
