"""
Wazobia Market price comparison — Step 3 (was Step 2): build the database
Loads the NORMALIZED combined data (from normalize.py) into SQLite.
Run normalize.py first — it produces combined_normalized.csv.
"""

from pathlib import Path
import pandas as pd
import sqlite3

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

# Define absolute paths using pathlib
CSV_PATH = BASE_DIR / "combined_normalized.csv"
DB_PATH = BASE_DIR / "prices.db"


def build_database():
    # Ensure the source file exists before trying to read it
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Could not find '{CSV_PATH.name}' at: {CSV_PATH}\n"
            f"Please run 'normalize.py' first to generate this file."
        )

    combined = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    combined.to_sql("prices", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Loaded {len(combined)} rows into {DB_PATH}")
    print(combined.groupby("business").size())


if __name__ == "__main__":
    build_database()
