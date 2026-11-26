"""Display helper only.

CV note: the analysis itself (cohorts, affinity/lift, levers, simulation) is done in SQL - see sql/q5, q8-q16.
This file only reshapes the SQL cohort output into a grid so it can be drawn as a heatmap.
"""


def retention_matrix(cohort_long):
    """Long SQL output (cohort, cohort_size, month_offset, retention_pct) -> grid of retention %."""
    ret = cohort_long.pivot(index="cohort", columns="month_offset", values="retention_pct")
    sizes = cohort_long.drop_duplicates("cohort").set_index("cohort")["cohort_size"]
    return ret, sizes   # months that have not happened yet stay blank (NaN), not 0
