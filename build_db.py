"""
Wazobia Market price comparison — Step 3 (was Step 2): build the database
Loads the NORMALIZED combined data (from normalize.py) into SQLite.
Run normalize.py first — it produces combined_normalized.csv.
"""

import pandas as pd
import sqlite3

DB_PATH = "prices.db"


def build_database():
    combined = pd.read_csv("combined_normalized.csv")

    conn = sqlite3.connect(DB_PATH)
    combined.to_sql("prices", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Loaded {len(combined)} rows into {DB_PATH}")
    print(combined.groupby("business").size())


if __name__ == "__main__":
    build_database()
