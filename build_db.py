"""
Wazobia Market price comparison — Step 2: build the database
Combines My Sasun (scraped) + Wazobia (manually entered) into one SQLite table.
"""

import pandas as pd
import sqlite3

DB_PATH = "prices.db"


def build_database():
    mysasun_df = pd.read_csv("mysasun_prices.csv")
    wazobia_df = pd.read_csv("wazobia_manual_prices.csv")

    # Drop rows where price wasn't filled in yet (still blank in the manual CSV)
    wazobia_df = wazobia_df.dropna(subset=["price"])

    combined = pd.concat([mysasun_df, wazobia_df], ignore_index=True)

    conn = sqlite3.connect(DB_PATH)
    combined.to_sql("prices", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Loaded {len(combined)} rows into {DB_PATH}")
    print(combined.groupby("business").size())


if __name__ == "__main__":
    build_database()
