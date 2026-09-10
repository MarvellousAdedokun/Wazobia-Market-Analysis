"""
Wazobia Market price comparison — Step 3: SQL analysis
Run real SQL queries against the SQLite database instead of pandas filtering.
"""

import sqlite3
import pandas as pd

DB_PATH = "prices.db"


def run_query(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# Average price per business, per product category
AVG_BY_CATEGORY = """
SELECT
    business,
    category,
    ROUND(AVG(price), 2) AS avg_price,
    COUNT(*) AS item_count
FROM prices
GROUP BY business, category
ORDER BY category, business;
"""

# Direct product-by-product comparison (only products both stores sell)
HEAD_TO_HEAD = """
SELECT
    m.product_name,
    m.price AS mysasun_price,
    w.price AS wazobia_price,
    ROUND(w.price - m.price, 2) AS price_difference
FROM prices m
JOIN prices w
    ON m.product_name = w.product_name
    AND m.business = 'My Sasun'
    AND w.business = 'Wazobia Market'
ORDER BY price_difference DESC;
"""

if __name__ == "__main__":
    print("=== Average price by category ===")
    print(run_query(AVG_BY_CATEGORY))

    print("\n=== Head-to-head product comparison ===")
    print(run_query(HEAD_TO_HEAD))
