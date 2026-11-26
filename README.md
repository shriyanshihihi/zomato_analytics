# Customer Loyalty & Retention Strategy - interview reconstruction (SQL + Cohort Analysis)

> **ALL DATA IS SYNTHETIC DEMO DATA.** It is not real Zomato data, and no number printed by this project is a
> real result or a number from the CV. The code reproduces the *method* described in the CV bullets so you can
> explain and demonstrate it. Behavioural effects are built into the generator as assumptions, so findings
> validate the pipeline, not the real world.

## CV bullets this project reconstructs
- Executed relational **SQL aggregation queries** to evaluate **expenditure patterns** and Gold subscription trends
- Identified **3 actionable retention levers** via cohort & affinity analysis to simulate roadmap for **30% Gold subscriber growth**

## Run it
```
pip install -r requirements.txt
python main.py                 # ~10 seconds, writes outputs/ and docs/
python main.py --users 8000 --seed 7 --capture 0.3 --uplift 0.3     # optional what-ifs
```
Python 3.9+, SQLite >= 3.25 (bundled with Python).

## Folder map
| Path | What it is |
|---|---|
| `main.py` | Entry point: loads data, runs the .sql files in order, draws charts |
| `sql/q1-q4` | Expenditure patterns + Gold trend (CV bullet 1) |
| `sql/q5, q8, q9` | Cohort retention, cuisine affinity, behaviour-to-Gold affinity (CV bullet 2) |
| `sql/q10, q13, q14` | Candidate levers, ranking, top 3 (CV bullet 2) |
| `sql/q11, q12, q15, q16` | Baseline, month-by-month simulation (recursive SQL), target check (CV bullet 2) |
| `src/data_gen.py` | Invents SYNTHETIC tables (stand-in for the real data) |
| `src/database.py` | Loads tables into SQLite, runs .sql files |
| `src/analysis.py`, `src/viz.py` | Display only: reshape cohort grid, draw charts/diagrams |
| `data/*.csv`, `outputs/` | Sample input and output (synthetic) |
| `docs/` | Diagrams, walkthrough, 4-page summary |

**Tooling note:** the analysis is SQL (matching the CV). Python is only the runner and the chart drawer.

## Pipeline in one paragraph
Generate data -> load into SQLite -> run SQL (monthly spend, spend quartiles, Gold trend, Gold vs non-Gold,
cohort activity, 30-day user features, renewal by usage) -> cohort retention %, affinity (**lift**) and
candidate levers are all computed in SQL; the top 3 are chosen in SQL -> a recursive SQL query projects
Gold members month by month with and without the levers and reports what lever strength would be needed
to reach +30%.

## 2-minute demo script
1. **Open** `docs/architecture.png` (15 s): "Data -> SQLite -> SQL queries -> cohort / affinity -> levers -> simulation."
2. **Run** `python main.py` in the terminal (10 s). Say what it is doing while it runs; point out the SYNTHETIC banner.
3. **Show SQL** `sql/q2_spend_quartiles.sql` (then `q12_simulate.sql` if asked about the simulation) (25 s): explain the JOIN, `GROUP BY`, `NTILE(4)` window, and why the
   LEFT JOIN uses a DISTINCT Gold list (avoid row multiplication).
4. **Show output** `outputs/chart_cohort_retention.png` and `q3_gold_trend.csv` (20 s): "rows are first-order cohorts,
   columns are months since first order; blanks are the future, not zero."
5. **Show** `sql/q6_user_features.sql` (20 s): "features come from days 0-30, the Gold outcome from days 30-90,
   so behaviour cannot be caused by Gold - that avoids reverse causality."
6. **Show** `outputs/lever_candidates.csv` + `chart_simulation.png` (30 s): "levers ranked by simulated gain; effect sizes are
   assumptions (`--capture`, `--uplift`); the useful output is the multiplier needed to hit +30%."
7. **Close** (10 s): one limitation - correlation is not causation, so each lever needs an A/B test.

## Honest limitations
Synthetic data; correlation not causation; lever effects are assumptions; levers overlap (the simulation adds them);
flat-inflow, no-seasonality model; no statistical confidence intervals on the simulation.
