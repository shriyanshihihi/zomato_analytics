"""Entry point.  python main.py            (about 10 seconds)

Read docs/PROJECT_WALKTHROUGH.md first - it explains every step in plain English.
Pipeline: synthetic data -> SQLite -> SQL queries -> cohort/affinity (SQL) -> levers (SQL) -> simulation (SQL) -> outputs.
Python only loads data, runs the .sql files in /sql and draws charts. The analysis itself is SQL (matches the CV: SQL, Cohort Analysis).
ALL NUMBERS PRODUCED ARE FROM SYNTHETIC DEMO DATA. They are not real results and not the CV's results.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from analysis import retention_matrix  # noqa: E402  (display helper only)
from data_gen import generate  # noqa: E402
from database import build_db, exec_sql, run_sql, table  # noqa: E402
import viz  # noqa: E402

TARGET = 30.0
HORIZON = 3  # months in the roadmap (one quarter)
RAMP = 3     # months over which lever effects phase in
SCENARIOS = {"Conservative": 0.5, "Base": 1.0, "Optimistic": 1.5}


def main(n_users, seed, outdir, capture, uplift):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    (ROOT / "data").mkdir(exist_ok=True)
    print(f"[1/7] Generating SYNTHETIC data: {n_users} users, seed={seed}  (stand-in for real tables: users, orders, subscriptions)")
    users, orders, subs = generate(n_users, seed)
    for name, df in (("users", users), ("orders", orders), ("subscriptions", subs)):
        df.to_csv(ROOT / "data" / f"{name}.csv", index=False)

    print("[2/7] Loading into SQLite (relational tables)")
    con = build_db(users, orders, subs, str(out / "demo.db"))

    print("[3/7] SQL aggregation queries  <- CV bullet 1: expenditure patterns + Gold trends")
    q1, q2 = run_sql(con, "q1_monthly_expenditure.sql"), run_sql(con, "q2_spend_quartiles.sql")
    q3, q4 = table(con, "gold_trend"), run_sql(con, "q4_gold_vs_nongold.sql")
    q7 = table(con, "renewal_bands")
    for n, d in (("q1_monthly_expenditure", q1), ("q2_spend_quartiles", q2), ("q3_gold_trend", q3),
                 ("q4_gold_vs_nongold", q4), ("q7_renewal_by_usage", q7)):
        d.to_csv(out / f"{n}.csv", index=False)

    print("[4/7] Cohort + affinity analysis (all in SQL)  <- CV bullet 2")
    q5 = run_sql(con, "q5_cohort_activity.sql"); q5.to_csv(out / "q5_cohort_activity.csv", index=False)
    ret, _ = retention_matrix(q5); ret.to_csv(out / "cohort_retention_matrix.csv")
    run_sql(con, "q8_cuisine_affinity.sql").to_csv(out / "cuisine_affinity_top15.csv", index=False)
    exec_sql(con, "q9_behaviour_affinity.sql")
    aff = table(con, "affinity").round(4); aff.to_csv(out / "behaviour_affinity.csv", index=False)
    exec_sql(con, "q10_lever_impact.sql", dict(capture=capture, uplift=uplift))

    print("[5/7] Ranking levers in SQL  <- CV bullet 2: '3 actionable retention levers'")
    base = run_sql(con, "q11_baseline_params.sql").iloc[0]
    sim_p = dict(G0=float(base.G0), n0=float(base.n0), g=float(base.g), horizon=HORIZON, ramp=RAMP)
    exec_sql(con, "q14_scenarios_standalone.sql")
    con.execute("DROP TABLE IF EXISTS sim_result"); exec_sql(con, "q12_simulate.sql", sim_p)
    con.execute("ALTER TABLE sim_result RENAME TO sim_standalone")
    exec_sql(con, "q13_lever_ranking.sql", dict(horizon=HORIZON))
    ranking = table(con, "lever_ranking").sort_values("gain_pct", ascending=False)
    ranking.round(3).to_csv(out / "lever_candidates.csv", index=False)
    top3 = ranking[ranking.is_top3 == 1]

    print("[6/7] Simulating roadmap in SQL  <- CV bullet 2: 'simulate roadmap for 30% Gold growth' (a TARGET, not a result)")
    con.execute("DROP TABLE scenarios"); exec_sql(con, "q15_scenarios_final.sql")
    con.execute("DROP TABLE IF EXISTS sim_result"); exec_sql(con, "q12_simulate.sql", sim_p)
    sim = table(con, "sim_result")
    need = run_sql(con, "q16_required_multiplier.sql", dict(horizon=HORIZON, target=TARGET)).iloc[0, 0]
    names = ["Baseline (no levers)", "Conservative", "Base", "Optimistic"]
    paths = {n: sim[sim.scenario == n].sort_values("t").members.tolist() for n in names}
    results = {n: round(float(sim[(sim.scenario == n) & (sim.t == HORIZON)].growth_pct.iloc[0]), 1) for n in names}

    print("[7/7] Writing charts + summary")
    viz.cohort_heatmap(ret, out / "chart_cohort_retention.png")
    viz.gold_trend(q3, out / "chart_gold_trend.png")
    viz.spend_quartiles(q2, out / "chart_spend_quartiles.png")
    viz.lever_chart(ranking, set(top3.name), out / "chart_levers.png")
    viz.scenarios(paths, base.G0 * (1 + TARGET / 100), out / "chart_simulation.png")
    viz.architecture(ROOT / "docs" / "architecture.png")
    viz.workflow(ROOT / "docs" / "workflow.png")

    summary = dict(
        DISCLAIMER="SYNTHETIC DEMO DATA - not real Zomato data, not the CV's real results",
        users=n_users, orders=len(orders), gold_terms=len(subs),
        baseline_gold_members_G0=int(base.G0), baseline_new_gold_per_month_n0=round(float(base.n0), 1),
        monthly_gold_lapse_rate_g=round(float(base.g), 4),
        assumptions=dict(capture=capture, uplift=uplift, ramp_months=RAMP, horizon_months=HORIZON),
        top3_levers=top3[["name", "type", "gain_pct"]].round(2).to_dict("records"),
        growth_pct_by_scenario=results, target_pct=TARGET,
        multiplier_on_lever_effects_needed_for_target=None if pd.isna(need) else float(need),
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
