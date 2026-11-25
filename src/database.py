"""SQLite layer.  CV link: the word 'relational' in bullet 1.

WHAT: puts the three DataFrames into a real SQL database (tables linked by user_id) and runs the
      .sql files in /sql, returning each result as a DataFrame.
WHY : so the "SQL aggregation queries" claim is real SQL run by a real SQL engine, not pandas
      pretending to be SQL.  SQLite is used because it needs no installation.
SAY : "users 1-to-many orders, users 1-to-many subscription terms, joined on user_id."
"""
import sqlite3
from pathlib import Path

import pandas as pd

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def build_db(users, orders, subs, db_path=":memory:"):
    if sqlite3.sqlite_version_info < (3, 25):
        raise RuntimeError("SQLite >= 3.25 needed for window functions (NTILE).")
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
    return con


def run_sql(con, filename):
    path = SQL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return pd.read_sql_query(path.read_text(), con)
