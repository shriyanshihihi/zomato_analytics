# Project walkthrough - read this if you do not remember what the code does

> All data is SYNTHETIC. The code reproduces the *method* in the CV; no printed number is a real result.

## The CV in one breath
"I used SQL to study how customers spend and how Gold membership trends, then used cohort and affinity
analysis to find 3 levers that raise retention, and simulated what it takes to reach 30% Gold growth."

## The story, start to end (what happens when you run `python main.py`)
Everything analytical is SQL. Python only loads the data, runs the .sql files and draws charts.
| # | Step | Plain English | Where | CV words it backs |
|---|------|---------------|-------|-------------------|
| 1 | Data | Three tables: users, orders, Gold subscription terms (invented here) | `src/data_gen.py` | (stand-in data) |
| 2 | Database | Load them into SQLite so they are *relational* tables joined on `user_id` | `src/database.py` | **relational** |
| 3 | SQL queries | Monthly spend, spend tiers, Gold trend, Gold vs non-Gold | `sql/q1-q4` | **SQL aggregation queries**, **expenditure patterns**, **Gold subscription trends** |
| 4 | Cohorts | Group users by first-order month; retention % per month | `sql/q5` | **cohort analysis** |
| 5 | Affinity | Which first-30-day behaviours go with joining Gold later? (lift) | `sql/q6, q8, q9` | **affinity analysis** |
| 6 | Levers | Each behaviour = candidate action; estimate impact; test each alone; keep top 3 | `sql/q10, q13, q14` | **3 actionable retention levers** |
| 7 | Simulation | Recursive SQL projects Gold members for 3 months; find lever strength for +30% | `sql/q11, q12, q15, q16` | **simulate roadmap**, **30% Gold subscriber growth** |

## Safe, honest answers to the usual probes
- **"Was 30% achieved?"** No claim. 30% is the target the simulation is tested against. The useful output is the *multiplier*: how strong the levers must be.
- **"What are your 3 levers?"** Use YOUR real ones. The code's three (on synthetic data) are cuisine discovery, delivery-fee burden, early order frequency. Each has a lift and a z-score.
- **"How do you know they work?"** We don't. Lift is association. Next step is an A/B test.
- **"Why first-30-day features and days 30-90 outcome?"** To stop leakage: Gold members pay 0 fees, which would fake a "fee-sensitive" signal.
- **"What did the cohort show?"** Biggest drop is month 0 to month 1; later months flatten. Blank cells are future months, not zeros.
- **"Where did the data come from?"** Say your real source truthfully. Do not imply internal company access unless true.

## Five formulas to remember
1. Retention(N) = users from cohort active in month N / cohort size
2. Lift = P(Gold | behaviour) / P(Gold)
3. Active Gold at month end = term start <= month end AND term end >= month end
4. Lapse rate g = lapsed terms / active Gold at previous month end
5. Members next month = members x (1 - g) + baseline joiners x (1 + lever uplift)   (recursive SQL, `q12`)

## Where to look when asked "show me"
SQL skill -> `sql/q2_spend_quartiles.sql` | cohorts -> `outputs/chart_cohort_retention.png` |
affinity -> `outputs/lever_candidates.csv` | simulation -> `sql/q12_simulate.sql` + `outputs/chart_simulation.png`
