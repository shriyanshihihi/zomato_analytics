"""Charts and diagrams (matplotlib). All charts are built from SYNTHETIC demo data."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

INK, MUTED, BLUE, ORANGE, GRID = "#1f2937", "#6b7280", "#2a6fdb", "#d9622b", "#e5e7eb"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "axes.axisbelow": True, "figure.dpi": 130})


def cohort_heatmap(ret, path):
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    im = ax.imshow(ret.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(ret.shape[1]), [f"M{c}" for c in ret.columns])
    ax.set_yticks(range(ret.shape[0]), ret.index)
    ax.grid(False)
    for i in range(ret.shape[0]):
        for j in range(ret.shape[1]):
            v = ret.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if v > 55 else INK)
    ax.set_title("Cohort retention % (users ordering in month N after first order) - synthetic data",
                 loc="left", color=INK, fontsize=10)
    ax.set_xlabel("Months since first order")
    ax.set_ylabel("First-order cohort")
    fig.colorbar(im, ax=ax, shrink=0.8, label="% of cohort")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def gold_trend(g, path):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(g.month, g.active_gold, color=BLUE, lw=2, marker="o", ms=5, label="Active Gold members (month end)")
    ax.bar(g.month, g.new_gold, color=ORANGE, width=0.5, label="New Gold members in month")
    ax.set_title("Gold subscription trend - synthetic data", loc="left", color=INK, fontsize=10)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def spend_quartiles(q, path):
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.bar([f"Q{int(x)}" for x in q.spend_quartile], q.pct_of_total_spend, color=BLUE, width=0.55)
    for i, (v, gld) in enumerate(zip(q.pct_of_total_spend, q.pct_ever_gold)):
        ax.text(i, v + 0.8, f"{v:.0f}% of spend\n{gld:.0f}% ever Gold", ha="center", fontsize=8, color=INK)
    ax.set_ylim(0, q.pct_of_total_spend.max() * 1.3)
    ax.set_ylabel("% of total spend")
    ax.set_title("Expenditure pattern: spend quartiles (Q4 = top) - synthetic data", loc="left", color=INK, fontsize=10)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def lever_chart(df, chosen, path):
    d = df.sort_values("gain_pct")
    fig, ax = plt.subplots(figsize=(7, 3.3))
    cols = [ORANGE if n in chosen else "#9ca3af" for n in d.name]
    ax.barh(d.name, d.gain_pct, color=cols, height=0.55)
    ax.set_xlabel("Standalone extra Gold growth by month 3 (percentage points, assumption-based)")
    ax.set_title("Candidate levers ranked (orange = chosen top 3) - synthetic data", loc="left", color=INK, fontsize=10)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def scenarios(paths, target_level, path):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    styles = {"Baseline (no levers)": ("#9ca3af", "-"), "Conservative": (BLUE, "--"),
              "Base": (BLUE, "-"), "Optimistic": (ORANGE, "-")}
    for name, p in paths.items():
        c, ls = styles[name]
        ax.plot(range(len(p)), p, color=c, ls=ls, lw=2, label=name)
    ax.set_xticks(range(len(p)))
    ax.axhline(target_level, color=INK, lw=1, ls=":")
    ax.text(0.1, target_level, " +30% target", va="bottom", fontsize=8, color=INK)
    ax.set_xlabel("Months from baseline (Sep-25)"); ax.set_ylabel("Active Gold members")
    ax.set_title("Roadmap simulation - ASSUMPTION-BASED, synthetic data", loc="left", color=INK, fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


# ------------------------------------------------------------------ diagrams
def _box(ax, x, y, w, h, text, fc="#eef4ff", ec=BLUE, fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", wrap=True)


def _arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.4))


def architecture(path):
    fig, ax = plt.subplots(figsize=(10, 5.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 5.6); ax.axis("off")
    ax.text(0.1, 5.3, "Architecture: Customer Loyalty & Retention Strategy (demo)", fontsize=12, fontweight="bold", color=INK)
    _box(ax, 0.2, 3.9, 2.2, 0.9, "1. DATA LAYER\nusers | orders | subscriptions\n(synthetic - data_gen.py)", "#f3f4f6", MUTED)
    _box(ax, 3.0, 3.9, 2.2, 0.9, "2. SQLite database\nload tables + indexes\n(database.py)", "#f3f4f6", MUTED)
    _box(ax, 5.8, 3.9, 3.9, 0.9, "3. SQL: aggregation + cohort + affinity + simulation (sql/q1..q16)\nGROUP BY, JOIN, NTILE, CTEs, recursive CTE", "#eef4ff", BLUE, bold=True)
    _arrow(ax, 2.4, 4.35, 3.0, 4.35); _arrow(ax, 5.2, 4.35, 5.8, 4.35)
    _box(ax, 0.2, 2.2, 2.9, 1.1, "4a. EXPENDITURE PATTERNS\nmonthly spend, AOV, spend tiers,\nfees as % of spend (q1,q2)", "#eef4ff", BLUE)
    _box(ax, 3.4, 2.2, 3.1, 1.1, "4b. COHORT ANALYSIS\nretention matrix by first-order\nmonth + Gold trend (q3,q5)", "#eef4ff", BLUE)
    _box(ax, 6.8, 2.2, 2.9, 1.1, "4c. AFFINITY ANALYSIS\nbehaviour -> Gold lift, cuisine\npairs, renewal by usage (q6,q7)", "#eef4ff", BLUE)
    for x in (1.65, 4.95, 8.25):
        _arrow(ax, 7.75, 3.9, x, 3.3)
    _box(ax, 1.5, 0.75, 3.2, 0.9, "5. LEVER IDENTIFICATION\nrank candidates, pick TOP 3\n(SQL q9, q10, q13)", "#fff1e8", ORANGE, bold=True)
    _box(ax, 5.3, 0.75, 3.4, 0.9, "6. ROADMAP SIMULATION\nproject Gold members, test\n+30% target (SQL q12, q16)", "#fff1e8", ORANGE, bold=True)
    for x in (1.65, 4.95, 8.25):
        _arrow(ax, x, 2.2, 3.1, 1.65)
    _arrow(ax, 4.7, 1.2, 5.3, 1.2)
    _box(ax, 3.2, 0.0, 3.6, 0.5, "7. OUTPUTS: CSV tables, charts (Python only draws), results.json", "#f3f4f6", MUTED)
    _arrow(ax, 7.0, 0.75, 6.2, 0.5)
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)


def workflow(path):
    fig, ax = plt.subplots(figsize=(10, 3.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 3.4); ax.axis("off")
    ax.text(0.1, 3.1, "End-to-end workflow: CV claim -> concept -> implementation -> output", fontsize=11, fontweight="bold", color=INK)
    steps = [("Raw tables\norders, users,\nsubscriptions", "#f3f4f6", MUTED),
             ("SQL aggregation\nGROUP BY / JOIN\n/ NTILE", "#eef4ff", BLUE),
             ("Expenditure\npatterns +\nGold trends", "#eef4ff", BLUE),
             ("Cohort +\naffinity\nanalysis", "#eef4ff", BLUE),
             ("3 retention\nlevers\n(ranked)", "#fff1e8", ORANGE),
             ("Simulation\nvs 30% Gold\ngrowth target", "#fff1e8", ORANGE)]
    w, gap = 1.45, 0.25
    for i, (t, fc, ec) in enumerate(steps):
        x = 0.15 + i * (w + gap)
        _box(ax, x, 1.1, w, 1.25, t, fc, ec, fs=8.5)
        if i:
            _arrow(ax, x - gap, 1.72, x, 1.72)
    ax.text(0.15, 0.55, "CV bullet 1: 'Executed SQL aggregation queries to evaluate expenditure patterns and Gold subscription trends' = steps 1-3",
            fontsize=8, color=INK)
    ax.text(0.15, 0.15, "CV bullet 2: 'Identified 3 actionable retention levers via cohort & affinity analysis to simulate roadmap for 30% Gold growth' = steps 4-6",
            fontsize=8, color=INK)
    fig.savefig(path, bbox_inches="tight"); plt.close(fig)
