"""SQLite layer.  CV link: the word 'relational' in bullet 1.

WHAT: puts the three DataFrames into a real SQL database (tables linked by user_id), then runs the
      .sql files in /sql. Python only RUNS the SQL; the analysis logic is in the .sql files.
WHY : so the "SQL aggregation queries" claim is real SQL run by a real SQL engine.
      SQLite is used only because it needs no installation (the SQL ideas are the same elsewhere).
SAY : "users 1-to-many orders, users 1-to-many subscription terms, joined on user_id."
"""
import sqlite3
from pathlib import Path

import pandas as pd

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

# SQL files that are saved as named VIEWS so later queries can reuse them (a view = a saved query)
VIEWS = {"gold_trend": "q3_gold_trend.sql",          # monthly Gold new/active/lapsed
         "user_features": "q6_user_features.sql",     # per-user first-30-day behaviour + Gold outcome
         "renewal_bands": "q7_renewal_by_usage.sql"}  # Gold renewal rate by usage


def _read(filename):
    path = SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text().strip().rstrip(";")


def build_db(users, orders, subs, db_path=":memory:"):
    if sqlite3.sqlite_version_info < (3, 35):
        raise RuntimeError("SQLite >= 3.35 needed (window functions + sqrt).")
    if db_path != ":memory:":
        Path(db_path).unlink(missing_ok=True)   # always start clean so re-runs never clash with old tables
    con = sqlite3.connect(db_path)
    for name, df in (("users", users), ("orders", orders), ("subscriptions", subs)):
        df.to_sql(name, con, index=False, if_exists="replace")
    months = pd.period_range("2025-01", "2025-09", freq="M")
    pd.DataFrame({
        "month": [str(m) for m in months],
        "month_start": [m.start_time.date().isoformat() for m in months],
        "month_end": [m.end_time.date().isoformat() for m in months],
    }).to_sql("months", con, index=False, if_exists="replace")
    con.executescript("""
        CREATE INDEX IF NOT EXISTS ix_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS ix_orders_date ON orders(order_date);
        CREATE INDEX IF NOT EXISTS ix_subs_user ON subscriptions(user_id);
    """)
    for view, f in VIEWS.items():
        con.execute(f"DROP VIEW IF EXISTS {view}")
        con.execute(f"CREATE VIEW {view} AS {_read(f)}")
    return con


def run_sql(con, filename, params=None):
    """Run a SELECT file and return a DataFrame."""
    return pd.read_sql_query(_read(filename), con, params=params or {})


def exec_sql(con, filename, params=None):
    """Run a CREATE TABLE ... AS file (results stay in the database for the next step)."""
    con.execute(_read(filename), params or {})
    con.commit()


def table(con, name):
    return pd.read_sql_query(f"SELECT * FROM {name}", con)
