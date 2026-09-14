"""
Wazobia Market price comparison — Step 4 (was Step 3): SQL analysis
Compares UNIT PRICE (price per gram/ml) across canonical items, not raw price
— this is what makes the comparison fair across different pack sizes.
"""

from pathlib import Path
import sqlite3
import pandas as pd

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "prices.db"


def run_query(query):
    # Ensure the database exists before querying
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database file not found at: {DB_PATH}\n"
            f"Please run 'build_db.py' first to initialize the database."
        )

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Average unit price per business, per canonical item
AVG_UNIT_PRICE = """
SELECT
    canonical_item,
    business,
    ROUND(AVG(unit_price), 5) AS avg_unit_price,
    COUNT(*) AS item_count
FROM prices
GROUP BY canonical_item, business
ORDER BY canonical_item, business;
"""

# Head-to-head: only items BOTH stores actually sell, with % difference
HEAD_TO_HEAD = """
SELECT
    m.canonical_item,
    ROUND(AVG(m.unit_price), 5) AS mysasun_unit_price,
    ROUND(AVG(w.unit_price), 5) AS wazobia_unit_price,
    ROUND(
        ((AVG(w.unit_price) - AVG(m.unit_price)) / AVG(m.unit_price)) * 100, 1
    ) AS pct_difference
FROM prices m
JOIN prices w
    ON m.canonical_item = w.canonical_item
    AND m.business = 'My Sasun'
    AND w.business = 'Wazobia Market'
GROUP BY m.canonical_item
ORDER BY pct_difference DESC;
"""

if __name__ == "__main__":
    print("=== Average unit price by canonical item and business ===")
    print(run_query(AVG_UNIT_PRICE).to_string())

    print("\n=== Head-to-head: items both stores sell (% difference) ===")
    result = run_query(HEAD_TO_HEAD)
    if result.empty:
        print("No overlapping canonical items yet — check that Wazobia's product_name "
              "text contains one of the same category keywords (garri, palm oil, "
              "egusi, etc.) as normalize.py looks for.")
    else:
        print(result.to_string())
